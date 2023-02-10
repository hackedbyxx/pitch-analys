function displayAlert(type, data, time) {
    var tip = document.createElement("div");
    if (type == "S") {
        tip.style.backgroundColor = "#009900";
    } else if (type == "E") {
        tip.style.backgroundColor = "#990000";
    } else if (type == "I") {
        tip.style.backgroundColor = " #e6b800";
    } else {
        console.log("入参type错误");
        return;
    }

    tip.id = "tip";
    tip.style.position = "absolute";
    tip.style.width = "15rem";
    // tip.style.height = "4rem";
    // tip.style.marginLeft = "-3rem";
    // tip.style.marginTop = "-1rem";
    tip.style.right = "5%";
    tip.style.bottom = "2rem";
    tip.style.color = "white";
    tip.style.fontSize = "20pt";
    tip.style.borderRadius = "5px";
    tip.style.textAlign = "center";
    tip.style.lineHeight = "3rem";
    tip.style.fontWeight = "bold";
    tip.style.whiteSpace = "pre-wrap"; //只对中文起作用，强制换行
    tip.style.wordWrap = "break-word" //只对英文起作用，以单词作为换行依据

    if (document.getElementById("tip") == null) {
        document.body.appendChild(tip);
        tip.innerHTML = data;
        setTimeout(function () {
            document.body.removeChild(tip);
        }, time);
    }
}