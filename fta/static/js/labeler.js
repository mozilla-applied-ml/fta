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
            position: options.position || "absolute",
            opacity: options.opacity || 0.6,
            "background-color": options.bgcolor || "yellow",
            "pointer-events": "none",
            "z-index": 9999,
            transition: options.transition || "all 150ms ease",
        },
    });
}

// Computes top/left/width/height position values corresponding to the displayed
// position of `innerRect`, which is relative to `outerRect`, but in the root
// document.
function outerRelativePositionFromInnerRect(outerRect, innerRect) {
    let result = {};
    result.top = Math.max(outerRect.top, outerRect.top + innerRect.top) + "px";
    result.left = Math.max(outerRect.left, outerRect.left + innerRect.left) + "px";
    result.width = (innerRect.right - Math.max(0, innerRect.left)) + "px";
    result.height = (innerRect.bottom - Math.max(0, innerRect.top)) + "px";
    return result;
}

// Positions (absolutely) `overlay` (lives in outer page) over `tracked_element`
// (lives in `iframe`).
function updateOverlayPosition(iframe, overlay, tracked_element) {
    const frameRect = iframe.getBoundingClientRect();
    const rect = tracked_element.getBoundingClientRect();
    const outerPosition = outerRelativePositionFromInnerRect(frameRect, rect);
    overlay.style.top = outerPosition.top;
    overlay.style.left = outerPosition.left;
    overlay.style.width = outerPosition.width;
    overlay.style.height = outerPosition.height;
}

function createOverlayForPickedElement(iframe, pickedElement, pickedElementsMap) {
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

    const removeButton = $new("button", {
        className: "remove-btn",
        type: "button",
        innerHTML: "Remove",
    });
    removeButton.addEventListener("click", function(e) {
        taggedOverlay.parentElement.removeChild(taggedOverlay);
        pickedElementsMap.delete(pickedElement);
    });

    innerDiv.appendChild(tagInput);
    innerDiv.appendChild(removeButton);
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

    // Track edits to input field in data-fathom attribute
    tagInput.addEventListener("input", function(e) {
        pickedElementsMap.get(pickedElement).tag = e.target.value;
    });

    return taggedOverlay;
}

function handleFormSubmit(iframe, pickedElementsMap) {
    let labelData = [];
    for (const [element, data] of pickedElementsMap) {
        const label = data.tag;
        if (label === "") {
            continue;
        }
        const id = uuidv4();
        element.dataset["fta_id"] = id;
        labelData.push({
            fta_id: id,
            label: data.tag
        });
    }
    document.querySelector("input[name='label-data']").value = JSON.stringify(labelData);
    document.querySelector("input[name='updated-sample']").value = iframe.contentDocument.documentElement.innerHTML;
}

// Create element picking and labeling UI for a loaded iframe
function createPickingUiForIframe({iframe, toggleBtn, submitBtn, startPicking = true}) {
    const subdoc = iframe.contentDocument;

    // Map of picked elements to corresponding overlay div
    let pickedElementsMap = new Map();

    // Controls element picker visibility
    let picking = startPicking;

    // Overlay element lives in this document to avoid polutting the iframe
    // document as much as possible. We simply reposition it over the
    // corresponding element in the iframe.
    let overlay = createOverlayDiv();
    document.body.appendChild(overlay);

    // Position overlay div over the hovered element
    function hoverHandler(e) {
        if (!picking) {
            return;
        }
        updateOverlayPosition(iframe, overlay, e.target);
    }

    // Stop element picker, set picked element and focus tag input
    function clickHandler(e) {
        if (!picking) {
            return;
        }
        // Prevent users from clicking links in captured bundles
        e.preventDefault();
        e.stopPropagation();
        if (!pickedElementsMap.has(e.target)) {
            const overlay = createOverlayForPickedElement(iframe, e.target, pickedElementsMap);
            overlay.querySelector(".tag-input").focus();
            pickedElementsMap.set(e.target, {
                overlay: overlay,
                tag: "",
            });
        }
    }

    for (const el of subdoc.body.querySelectorAll("*")) {
        // Install handlers for picking new elements
        el.addEventListener("mouseover", hoverHandler);
        el.addEventListener("click", clickHandler);

        //TODO: makes this work with an external labelData
        // // Highlight existing tagged elements
        // if (el.dataset.fathom) {
        //     const overlay = createOverlayForPickedElement(iframe, el, pickedElementsMap);
        //     pickedElementsMap.set(el, overlay);
        // }
    }

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
