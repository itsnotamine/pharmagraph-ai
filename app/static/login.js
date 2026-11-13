const form = document.getElementById("login-form");
const error = document.getElementById("login-error");
const button = document.getElementById("login-button");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    error.textContent = "";
    button.disabled = true;
    button.textContent = "Signing in...";

    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value;

    try {
        const response = await fetch("/auth/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "same-origin",
            body: JSON.stringify({ email, password })
        });

        if (!response.ok) {
            throw new Error(
                response.status === 401
                    ? "Invalid email or password."
                    : "Unable to sign in. Please try again."
            );
        }

        window.location.assign("/");

    } catch (err) {
        error.textContent = err.message;
    } finally {
        button.disabled = false;
        button.textContent = "Sign In →";
    }
});

/* Refresh personalized greeting after browser autofill */
window.addEventListener("pageshow", () => {
    updateWelcomeMessage();
    setTimeout(updateWelcomeMessage, 300);
    setTimeout(updateWelcomeMessage, 1000);
});

emailInput.addEventListener("change", updateWelcomeMessage);
emailInput.addEventListener("blur", updateWelcomeMessage);
