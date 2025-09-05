document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("login-form");

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        const username = document.getElementById("username").value.trim();
        const password = document.getElementById("password").value.trim();

        fetch("http://localhost:5000/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",  // important for Flask session
            body: JSON.stringify({ username, password })
        })
        .then(res => res.json())
        .then(data => {
            if (data.message) {
                alert(data.message);
                window.location.href = "index.html"; // redirect after login
            } else {
                alert(data.error || "Login failed");
            }
        })
        .catch(err => console.error("Error:", err));
    });
});
