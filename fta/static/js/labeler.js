import { v4 as uuidv4 } from "https://jspm.dev/uuid@8.3.1";

// Create a new DOM element with tag `tag`, set attributes in `attrs`.
// If `attrs` contains inner objects that exist in the created element, recurse
// and set nested properties, eg. element.style.display.
function $new(tag, attrs)
{
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

function createOverlayDiv(options)
{
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
function outerRelativePositionForElement(element)
{
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

    const outermostRect = current.getBoundingClientRect();

    // Remove section hidden by scrolled outermost iframe
    if (outermostRect.top > result.top) {
        result.height -= outermostRect.top - result.top;
    }

    // Clamp top to outermost iframe
    result.top = Math.max(result.top, outermostRect.top);

    return result;
}

// Positions (absolutely) `overlay` (lives in outer page) over `tracked_element`
// (lives in `iframe` - potentially in a nested iframe).
function updateOverlayPosition(iframe, overlay, tracked_element)
{
    const absolutePos = outerRelativePositionForElement(tracked_element);
    overlay.style.top = absolutePos.top + "px";
    overlay.style.left = absolutePos.left + "px";
    overlay.style.width = absolutePos.width + "px";
    overlay.style.height = absolutePos.height + "px";
}

function createOverlayForPickedElement(iframe, pickedElement, pickedElementsMap, remover=true)
{
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

function handleFormSubmit(iframe, pickedElementsMap)
{
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
    document.querySelector("input[name='updated-sample']").value = iframe.contentDocument.documentElement.outerHTML;
}

// For all elements of preExistingLables in this iframe, add overlay.
// Overlay does not have a remove button. Tags can only be removed through backend.
function createOverlaysForPreExistingLabels({
        // HTMLIFrameElement
        iframe,
        // List of pre-existing labels ({fta_id, label} objects)
        preExistingLabels,
        // Map of picked elements to corresponding overlay div, will be modified
        pickedElementsMap
    })
{
    for (const [fta_id, label] of preExistingLabels) {
        const el = iframe.contentDocument.body.querySelector("[data-fta_id='" + fta_id + "']");
        if (el) {
            const overlay = createOverlayForPickedElement(
                iframe, element, pickedElementsMap, /*remover=*/false
            );
            overlay.querySelector(".tag-input").value = label;
            pickedElementsMap.set(element, {
                overlay: overlay,
                tag: label,
            });
        }
    }
}

// Detecting when iframes are (fully) loaded is frail with race conditions
// This code is extremely hacky with timeouts and intervals, but it's the only
// way to make it reliable against all possible timings.
function callWhenLoaded(iframe, callback) {
    // IFrame has a document
    if (iframe.contentDocument !== null) {
        // ...but body is still null, loading
        if (iframe.contentDocument.body === null) {
            // We try until body is non null
            const interval = setInterval(function() {
                if (iframe.contentDocument.body !== null) {
                    clearInterval(interval);
                    callback();
                }
            }, 100);
        } else {
            // ...body is non null, but it can still not have its children
            // elements, so we give the event loop some time. This could still
            // break given that it's a single timeout with a fixed time but
            // there's no way to directly test if the iframe is fully loaded.
            setTimeout(function() {
                callback();
            }, 100);
        }
    } else {
        // IFrame doesn't have a document, so we wait for the load event, this
        // is the simple case.
        iframe.addEventListener("load", function() {
            callback()
        });
    }
}

// Create element picking and labeling UI for a potentially still loading iframe
function createPickingUiForIframe({
        // HTMLIFrameElement
        iframe,
        // Toggle picker on and off
        toggleBtn,
        // Form submit button
        submitBtn,
        // Should picker be active on launch
        startPicking=true,
        // List of pre-existing labels to display in page ({fta_id, label} keys)
        preExistingLabels=[],
    })
{
    callWhenLoaded(iframe, function() {
        createPickingUiForLoadedIframe({
          iframe, toggleBtn, submitBtn, startPicking
        });
    });
}

// Create element picking and labeling UI for a loaded iframe
function createPickingUiForLoadedIframe({
        // HTMLIFrameElement
        iframe,
        // Toggle picker on and off
        toggleBtn,
        // Form submit button
        submitBtn,
        // Should picker be active on launch
        startPicking=true,
        // List of pre-existing labels to display in page ({fta_id, label} keys)
        preExistingLabels=[],
    })
{
    const subdoc = iframe.contentDocument;
    let picking = startPicking;

    // Map of picked elements to corresponding overlay div
    let pickedElementsMap = new Map();

    // Overlay element lives in this document to avoid polutting the iframe
    // document as much as possible. We simply reposition it over the
    // corresponding element in the iframe.
    let overlay = createOverlayDiv();
    let currentlyHovered = subdoc.body;
    document.body.appendChild(overlay);

    createOverlaysForPreExistingLabels({
        iframe,
        preExistingLabels,
        pickedElementsMap,
    });

    // Position overlay div over the hovered element
    function hoverHandler(e) {
        if (!picking) {
            return;
        }
        currentlyHovered = e.target;
        updateOverlayPosition(iframe, overlay, currentlyHovered);
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
            if (el instanceof HTMLIFrameElement) {
                callWhenLoaded(el, function() {
                    hookAllElements(el.contentDocument.body);
                    updateOverlaysOnScroll(el.contentWindow);
                });
            } else {
                el.addEventListener("mouseover", hoverHandler);
                el.addEventListener("click", clickHandler);
            }
        }
    }

    // Install handlers for picking new elements, recursing into nested iframes
    hookAllElements(subdoc.body);

    // Update fixed overlays when parent document is scrolled
    function updateOverlaysOnScroll(win) {
        let ticking = false;
        win.addEventListener("scroll", function(e) {
            if (!ticking) {
                window.requestAnimationFrame(function() {
                    for (const [element, {overlay, tag}] of pickedElementsMap) {
                        updateOverlayPosition(iframe, overlay, element);
                    }
                    updateOverlayPosition(iframe, overlay, currentlyHovered);
                    ticking = false;
                });

                ticking = true;
            }
        });
    }

    updateOverlaysOnScroll(window);
    updateOverlaysOnScroll(iframe.contentWindow);

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

    document.querySelector(".picker-loading-overlay").classList.add("hidden");
}

export { createPickingUiForIframe };
