// Login JavaScript Integration 

document.getElementById("loginForm").addEventListener("submit", function(e) {
    e.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    fetch("/auth/api/login/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            email: email,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.access) {
            // Save tokens in localStorage
            localStorage.setItem("access_token", data.access);
            localStorage.setItem("refresh_token", data.refresh);

            alert("Login successful!");
            
            // ✅ Redirect to home page instead of dashboard
            window.location.href = "/";  // <-- change here
        } else {
            alert("Invalid credentials");
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });
});






// Sign JavaScript Integration 

document.getElementById("signupForm").addEventListener("submit", function(e) {
    e.preventDefault();  // prevent page reload

    const full_name = document.getElementById("full_name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    fetch("/api/signup/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            full_name: full_name,
            email: email,
            password: password
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert("Account created successfully!");

            // ✅ Redirect to login page
            window.location.href = "/login/";
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
logoutBtn.addEventListener("click", async function(e) {
    e.preventDefault();
    const refreshToken = localStorage.getItem("refresh_token");

    if (!refreshToken) {
        // fallback: just clear local storage
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        updateNavbar();
        return;
    }

    try {
        const response = await fetch("/api/logout/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (response.ok) {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            updateNavbar();
        } else {
            console.error("Logout failed");
        }
    } catch (err) {
        console.error("Logout error:", err);
    }
});
