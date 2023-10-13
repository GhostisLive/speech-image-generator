function getPositionAtCenter(element) {
  const {left, right} = element.getBoundingClientRect();
  return {
    left, 
    right
  };
}

function getDistanceBetweenElements(a, b) {
 const aPosition = getPositionAtCenter(a);
 const bPosition = getPositionAtCenter(b);

 return aPosition.right - bPosition.left;  
}

//Fix logout button width

const dropdownLabel = document.getElementById("dropdownlabel");
if (dropdownLabel) {
  const loginBtn = document.getElementById("loginbtn");
  const PIXELS_PER_CHAR = 8.8235294117647058823529411764706;
  loginBtn.style.width = `${Math.round(PIXELS_PER_CHAR * dropdownLabel.innerHTML.length)}px`;
}
