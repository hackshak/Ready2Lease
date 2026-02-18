// Login JavaScript Integration 
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

document.getElementById("loginForm").addEventListener("submit", function(e) {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    fetch("/auth/api/login/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            email: email,
            password: password
        }),
        credentials: "same-origin"  
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            window.location.href = "/dashboard/home/";
        } else {
            alert("Invalid credentials");
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });
});







// Sign JavaScript Integration 
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

document.getElementById("signupForm").addEventListener("submit", function(e) {
    e.preventDefault();

    const full_name = document.getElementById("full_name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    fetch("/auth/api/signup/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCookie("csrftoken")
        },
        body: JSON.stringify({
            full_name: full_name,
            email: email,
            password: password
        }),
        credentials: "same-origin"  // ✅ Required for session
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            // 🔥 User is already logged in
            window.location.href = "/dashboard/home/";
        } else {
            alert("Error creating account");
            console.log(data);
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });
});





// Logout Api
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

logoutBtn.addEventListener("click", async function(e) {
    e.preventDefault();

    try {
        const response = await fetch("/auth/api/logout/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCookie("csrftoken")
            },
            credentials: "same-origin"
        });

        if (response.ok) {
            // Redirect to login page after logout
            window.location.href = "/auth/login/";
        } else {
            console.error("Logout failed");
        }

    } catch (err) {
        console.error("Logout error:", err);
    }
});

