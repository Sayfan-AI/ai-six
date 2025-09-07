document.addEventListener("DOMContentLoaded", () => {
    console.log('HOOK STARTED!');

    // This selector/document structure may be specific to the `furo` html theme.
    const sidebarLinks = document.querySelectorAll(".sidebar-tree a");

    sidebarLinks.forEach(link => {
        const text = link.textContent.trim();
        const parts = text.split(".");
        if (parts.length > 1) {
            link.textContent = parts[parts.length - 1]; // keep only last part
        }
        console.log(text);
    });
});
