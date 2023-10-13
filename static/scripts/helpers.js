function setTextForTime(element, data, time = 3000) {
    element.innerHTML = data;

    if (window.safeLimit)
        clearTimeout(window.safeLimit);

    window.safeLimit = setTimeout(() => {
        element.innerHTML = "";
        delete window.safeLimit;
    }, time);
}
