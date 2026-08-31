const form = document.getElementById("vulnerabilityForm");
const output = document.getElementById("output");

const createSubmissionCounter = () => {
    let count = 0;

    return () => {
        count = count + 1;
        return count;
    };
};

const countSubmission = createSubmissionCounter();

const validateForm = () => {
    const description = document.getElementById("description").value.trim();
    const termsAccepted = document.getElementById("termsAccepted").checked;

    if (description.length <= 25) {
        alert("Description must contain more than 25 characters.");
        document.getElementById("description").focus();
        return false;
    }

    if (!termsAccepted) {
        alert("You must agree to the terms and conditions.");
        document.getElementById("termsAccepted").focus();
        return false;
    }

    return true;
};

form.addEventListener("submit", (event) => {
    event.preventDefault();

    if (!validateForm()) {
        return;
    }

    const formData = {
        vulnerabilityTitle: document.getElementById("vulnerabilityTitle").value.trim(),
        packageName: document.getElementById("packageName").value.trim(),
        submitterEmail: document.getElementById("submitterEmail").value.trim(),
        description: document.getElementById("description").value.trim(),
        category: document.getElementById("category").value,
        termsAccepted: document.getElementById("termsAccepted").checked
    };

    const jsonString = JSON.stringify(formData);
    console.log("JSON string:", jsonString);

    const parsedObject = JSON.parse(jsonString);

    const { vulnerabilityTitle, submitterEmail } = parsedObject;
    console.log("Primary field:", vulnerabilityTitle);
    console.log("Email field:", submitterEmail);

    const updatedObject = {
        ...parsedObject,
        submissionDate: new Date().toLocaleString()
    };

    console.log("Updated object:", updatedObject);

    const submissionCount = countSubmission();
    console.log("Successful submission count:", submissionCount);

    output.textContent = JSON.stringify(updatedObject, null, 2);
    form.reset();
});