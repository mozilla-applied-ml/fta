import { v4 as uuidv4 } from "https://jspm.dev/uuid@8.3.1";

// Create a new DOM element with tag `tag`, set attributes in `attrs`.
// If `attrs` contains inner objects that exist in the created element, recurse
// and set nested properties, eg. element.style.display.
function $new(tag, attrs) {
    function set_attrs(target, attrs) {
        for (const property in attrs) {
            if (typeof attrs[property] === "object" && typeof target[property] !== "undefined") {
                set_attrs(target[property], attrs[property]);
            } else {
                target[property] = attrs[property];
            }
        }
    }
    let el = document.createElement(tag);
    set_attrs(el, attrs);
    return el;
}

function createOverlayDiv(options) {
    options = options || {};
    return $new("div", {
        style: {
            position: options.position || "fixed",
            opacity: options.opacity || 0.6,
            "background-color": options.bgcolor || "yellow",
            "pointer-events": "none",
            "z-index": 9999,
            transition: options.transition || "all 150ms ease",
        },
    });
}

// Computes top/left/width/height position values relative to outer viewport for
// the `element` element, which may be nested several iframes deep.
function outerRelativePositionForElement(element) {
    const rect = element.getBoundingClientRect();
    let result = {
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height
    };

    let current = null;
    let next = element.ownerDocument.defaultView.frameElement;
    do {
        current = next;
        next = current.ownerDocument.defaultView.frameElement;
        const frameRect = current.getBoundingClientRect();
        result.top = result.top + frameRect.top;
        result.left = result.left + frameRect.left;
    } while (next !== null);

    return result;
}

// Positions (absolutely) `overlay` (lives in outer page) over `tracked_element`
// (lives in `iframe`).
function updateOverlayPosition(iframe, overlay, tracked_element) {
    const absolutePos = outerRelativePositionForElement(tracked_element);
    overlay.style.top = absolutePos.top + "px";
    overlay.style.left = absolutePos.left + "px";
    overlay.style.width = absolutePos.width + "px";
    overlay.style.height = absolutePos.height + "px";
}

function createOverlayForPickedElement(iframe, pickedElement, pickedElementsMap, remover=true) {
    const taggedOverlay = createOverlayDiv({
        bgcolor: "red",
        transition: "none", // These should track scrolling without animations
    });

    // Inner div to display tag value with text input and remove button
    const innerDiv = $new("div", {
        style: {
            position: "relative",
            width: "6em",
            "pointer-events": "auto",
        },
    });

    const tagInput = $new("input", {
        className: "tag-input",
        type: "text",
        style: "width: 100%; min-width: 10em;",
        value: "",
    });
    innerDiv.appendChild(tagInput);

    if (remover) {
        const removeButton = $new("button", {
            className: "remove-btn",
            type: "button",
            innerHTML: "Remove",
        });
        removeButton.addEventListener("click", function(e) {
            taggedOverlay.parentElement.removeChild(taggedOverlay);
            pickedElementsMap.delete(pickedElement);
        });
        innerDiv.appendChild(removeButton);
    }

    taggedOverlay.appendChild(innerDiv);

    // Position overlay over picked element
    updateOverlayPosition(iframe, taggedOverlay, pickedElement);
    document.body.appendChild(taggedOverlay);

    // Track iframe scroll and update overlay position accordingly
    let ticking = false;
    iframe.contentWindow.addEventListener("scroll", function(e) {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                updateOverlayPosition(iframe, taggedOverlay, pickedElement);
                ticking = false;
            });

            ticking = true;
        }
    });

    // Track edits to input field in data-fta_id attribute
    tagInput.addEventListener("input", function(e) {
        pickedElementsMap.get(pickedElement).tag = e.target.value;
    });

    return taggedOverlay;
}

function handleFormSubmit(iframe, pickedElementsMap) {
    let labelData = [];
    let id = '';

    for (const [element, data] of pickedElementsMap) {
        const label = data.tag;
        if (label === "") {
            continue;
        }
        if (element.dataset.hasOwnProperty('fta_id')) {
            id = element.dataset.fta_id;
        } else {
            id = uuidv4();
            element.dataset["fta_id"] = id;
        }
        labelData.push({
            fta_id: id,
            label: data.tag
        });
    }
    document.querySelector("input[name='label-data']").value = JSON.stringify(labelData);
    document.querySelector("input[name='updated-sample']").value = iframe.contentDocument.documentElement.innerHTML;
}

// Create element picking and labeling UI for a loaded iframe
function createPickingUiForIframe({
        // iFrame content
        iframe,
        // Toggle picker on and off
        toggleBtn,
        // Form submit button
        submitBtn,
        // Map of picked elements to corresponding overlay div
        pickedElementsMap=new Map(),
        // Should picker be active on launch
        startPicking=true,
    }) {

    const subdoc = iframe.contentDocument;
    let picking = startPicking;

    // Overlay element lives in this document to avoid polutting the iframe
    // document as much as possible. We simply reposition it over the
    // corresponding element in the iframe.
    let overlay = createOverlayDiv();
    document.body.appendChild(overlay);


    // For all elements of pickedElementsMap, add overlay
    // Overlay does not have a remove button. Tags can only be
    // removed through back end.
    pickedElementsMap.forEach(({overlay, tag}, element) => {
        if (element.dataset.fta_id) {
            let overlay = createOverlayForPickedElement(
                iframe, element, pickedElementsMap, false
            );
            overlay.querySelector(".tag-input").value = tag;
            pickedElementsMap.set(element, {
                overlay: overlay,
                tag: tag,
            });
        }
    });


    // Position overlay div over the hovered element
    function hoverHandler(e) {
        if (!picking) {
            return;
        }
        updateOverlayPosition(iframe, overlay, e.target);
    }

    // Stop element picker, set picked element and focus tag input
    function clickHandler(e) {
        // Always prevent users from clicking links in captured bundles
        e.preventDefault();
        e.stopPropagation();

        if (!picking) {
            return;
        }

        // Create empty overlays if picking and not already in map
        if (!pickedElementsMap.has(e.target)) {
            const overlay = createOverlayForPickedElement(iframe, e.target, pickedElementsMap);
            overlay.querySelector(".tag-input").focus();
            pickedElementsMap.set(e.target, {
                overlay: overlay,
                tag: "",
            });
        }
    }

    function hookAllElements(body) {
        for (const el of body.querySelectorAll("*")) {
            if (el instanceof HTMLIFrameElement && el.contentDocument !== null) {
                hookAllElements(el.contentDocument.body);
            } else {
                el.addEventListener("mouseover", hoverHandler);
                el.addEventListener("click", clickHandler);
            }
        }
    }

    // Install handlers for picking new elements, recursing into nested iframes
    hookAllElements(subdoc.body);

    // Update fixed overlays when parent document is scrolled
    let ticking = false;
    window.addEventListener("scroll", function(e) {
        if (!ticking) {
            window.requestAnimationFrame(function() {
                for (const [element, {overlay, tag}] of pickedElementsMap) {
                    updateOverlayPosition(iframe, overlay, element);
                }
                ticking = false;
            });

            ticking = true;
        }
    });

    if (typeof toggleBtn !== "undefined") {
        toggleBtn.addEventListener("click", function() {
            picking = !picking;
            if (!picking) {
                overlay.style.width = "0px";
                overlay.style.height = "0px";
            }
        });
    }

    if (typeof submitBtn !== "undefined") {
        submitBtn.addEventListener("click", function() {
            handleFormSubmit(iframe, pickedElementsMap);
        });
    }
}

export { createPickingUiForIframe };
