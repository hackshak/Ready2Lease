function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.getElementById("forgotPasswordForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const email = document.getElementById("email").value;

    const response = await fetch("/auth/api/password-reset/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({ email }),
        credentials: "same-origin"
    });

    const data = await response.json();

    if (response.ok) {
        window.location.href = `/reset-password-confirm/${data.uid}/`;
    } else {
        alert(data.detail || "Email not found");
    }
});
