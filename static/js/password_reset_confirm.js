document.getElementById("resetPasswordForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const password = document.getElementById("password").value;

    // Get UID from URL
    const pathParts = window.location.pathname.split("/");
    const uid = pathParts[pathParts.length - 2];

    const response = await fetch("/auth/api/reset-password-confirm/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            uid: uid,
            password: password
        }),
        credentials: "same-origin"
    });

    const data = await response.json();

    if (response.ok) {
        alert("Password reset successful!");
        window.location.href = "/auth/login/";
    } else {
        alert("Error resetting password");
        console.log(data);
    }
});
