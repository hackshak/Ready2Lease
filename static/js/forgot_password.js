document.getElementById("forgotPasswordForm").addEventListener("submit", async function(e) {
    e.preventDefault();
    const email = document.getElementById("email").value;

    const response = await fetch("{% url 'api-password-reset' %}", { // ✅ template tag works here
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email })
    });

    const data = await response.json();
    if (response.ok) {
        window.location.href = `/reset-password-confirm/${data.uid}/`;
    } else {
        alert(data.detail || "Email not found");
    }
});
