const form = document.getElementById("vulnerabilityForm");
const output = document.getElementById("output");

form.addEventListener("submit", function (event) {
    event.preventDefault();

    const description = document.getElementById("description").value.trim();

    if (description.length <= 25) {
        output.textContent = "Description must contain more than 25 characters.";
        document.getElementById("description").focus();
        return;
    }

    const report = {
        vulnerabilityTitle: document.getElementById("vulnerabilityTitle").value.trim(),
        packageName: document.getElementById("packageName").value.trim(),
        submitterEmail: document.getElementById("submitterEmail").value.trim(),
        description: description,
        category: document.getElementById("category").value,
        termsAccepted: document.getElementById("termsAccepted").checked,
        submissionDate: new Date().toLocaleString()
    };

    output.textContent = JSON.stringify(report, null, 2);
    form.reset();
});