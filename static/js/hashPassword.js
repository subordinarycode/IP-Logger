async function hashPassword(event) {
    event.preventDefault(); // Prevent the default form submission

    // Check if the Web Crypto API is supported
    if (!window.crypto || !window.crypto.subtle) {
        alert('Crypto API is not supported in your browser.');
        return;
    }

    // Get the password input value
    const passwordInput = document.getElementById('password');
    const password = passwordInput.value.trim(); // Trim whitespace

    // Validate the password input
    if (!password) {
        alert('Please enter a password.');
        return;
    }

    // Encode the password and generate the hash
    const encoder = new TextEncoder();
    const data = encoder.encode(password);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');

    // Create a hidden input to store the hashed password
    const form = event.target;
    const hashedInput = document.createElement('input');
    hashedInput.type = 'hidden';
    hashedInput.name = 'password'; // Ensure this matches your server-side expectations
    hashedInput.value = hashHex;
    form.appendChild(hashedInput);

    // Debugging statement
    console.log("Form is being submitted with hashed password:", hashHex);

    // Submit the form
    form.submit();
}
