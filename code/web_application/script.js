const form = document.getElementById("vulnerabilityForm");
const searchForm = document.getElementById("searchForm");
const clearSearchButton = document.getElementById("clearSearch");

const output = document.getElementById("output");
const recordList = document.getElementById("recordList");
const loadingState = document.getElementById("loadingState");
const emptyState = document.getElementById("emptyState");
const errorState = document.getElementById("errorState");

const escapeHtml = (value) => {
    const element = document.createElement("div");
    element.textContent = value ?? "";
    return element.innerHTML;
};

const setState = (state) => {
    loadingState.hidden = state !== "loading";
    emptyState.hidden = state !== "empty";
    errorState.hidden = state !== "error";
};

const renderRecords = (records) => {
    recordList.innerHTML = records
        .map(
            (record) => `
                <article class="record-card">
                    <h3>${escapeHtml(record.vulnerabilityTitle)}</h3>
                    <p><strong>Package:</strong> ${escapeHtml(record.packageName)}</p>
                    <p><strong>Category:</strong> ${escapeHtml(record.category)}</p>
                    <p><strong>Submitter:</strong> ${escapeHtml(record.submitterEmail)}</p>
                    <p><strong>Description:</strong> ${escapeHtml(record.description)}</p>
                    <p><strong>Record ID:</strong> ${record.id}</p>
                </article>
            `
        )
        .join("");
};

const loadRecords = async (search = "") => {
    setState("loading");
    recordList.innerHTML = "";

    try {
        const query = search.trim()
            ? `?search=${encodeURIComponent(search.trim())}`
            : "";

        const response = await fetch(`/api/reports${query}`);

        if (!response.ok) {
            throw new Error("The reports could not be loaded.");
        }

        const records = await response.json();

        if (records.length === 0) {
            setState("empty");
            return;
        }

        setState("none");
        renderRecords(records);
    } catch (error) {
        setState("error");
        output.textContent = error.message;
    }
};

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

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!validateForm()) {
        return;
    }

    const formData = {
        vulnerabilityTitle: document
            .getElementById("vulnerabilityTitle")
            .value.trim(),
        packageName: document.getElementById("packageName").value.trim(),
        submitterEmail: document
            .getElementById("submitterEmail")
            .value.trim(),
        description: document.getElementById("description").value.trim(),
        category: document.getElementById("category").value,
        termsAccepted: document.getElementById("termsAccepted").checked,
    };

    try {
        const response = await fetch("/api/reports", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(formData),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || "The report could not be submitted.");
        }

        output.textContent = JSON.stringify(result, null, 2);
        form.reset();

        await loadRecords();
    } catch (error) {
        output.textContent = error.message;
        setState("error");
    }
});

searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const searchValue = document.getElementById("searchInput").value;
    await loadRecords(searchValue);
});

clearSearchButton.addEventListener("click", async () => {
    document.getElementById("searchInput").value = "";
    await loadRecords();
});

loadRecords();