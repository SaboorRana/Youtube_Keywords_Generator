function toggleMenu() {
    document.querySelector(".nav-links").classList.toggle("active");
}

function generateKeywords() {
    let title = document.getElementById("title").value.trim();
    let description = document.getElementById("description").value.trim();

    if (!title) {
        alert("Please enter a title!");
        return;
    }

    let keywords = title.split(" ").concat(description ? description.split(" ") : []);
    keywords = [...new Set(keywords.map(word => word.toLowerCase()))]; // Remove duplicates

    let keywordBox = document.getElementById("keyword-box");
    keywordBox.innerHTML = keywords.join(", ");

    document.getElementById("result-container").style.display = "block";
}
