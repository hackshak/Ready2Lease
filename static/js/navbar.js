// Navbar JS for toggling menu
const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelector('.nav-links');

hamburger.addEventListener('click', () => {
    navLinks.classList.toggle('active');
});




// Update login and signup buttons in navbar based on users authentication
document.addEventListener("DOMContentLoaded", function() {
    const loginBtn = document.querySelector(".nav-btn-login");
    const signupBtn = document.querySelector(".nav-btn-signup");
    const logoutBtn = document.getElementById("logoutBtn");

    function updateNavbar() {
        const accessToken = localStorage.getItem("access_token");

        if (accessToken) {
            loginBtn.style.display = "none";
            signupBtn.style.display = "none";
            logoutBtn.style.display = "inline-block"; // show logout
        } else {
            loginBtn.style.display = "inline-block";
            signupBtn.style.display = "inline-block";
            logoutBtn.style.display = "none"; // hide logout
        }
    }

    // Handle logout click
    logoutBtn.addEventListener("click", function(e) {
        e.preventDefault();
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        updateNavbar();
    });

    // Initial check
    updateNavbar();

    // Listen for login changes in other tabs
    window.addEventListener("storage", function(event) {
        if (event.key === "access_token") updateNavbar();
    });
});


