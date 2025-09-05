document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("signup-form");

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        fetch("http://localhost:5000/signup", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",
            body: JSON.stringify({ username, password })
        })
        .then(res => res.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                window.location.href = "index.html"; // go to index after signup
            } else {
                alert(data.error || "Signup failed");
            }
        })
        .catch(err => console.error("Error:", err));
    });
});
