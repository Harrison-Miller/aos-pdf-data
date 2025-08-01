// Function to sanitize IDs for valid CSS selectors
function sanitizeId(text) {
    return text.replace(/[^a-zA-Z0-9\-]/g, '-').toLowerCase();
}

// Function to render FAQ data as nested cards
function renderFAQ(data) {
    const container = document.createElement('div');
    container.className = 'faq-container';

    data.forEach(section => {
        // Create section card
        const sectionCard = document.createElement('div');
        sectionCard.className = 'faq-section';
        sectionCard.id = sanitizeId(section.title); // Generate a sanitized ID for the section

        const sectionTitle = document.createElement('h2');
        const sectionLink = document.createElement('a');
        sectionLink.href = `#${sectionCard.id}`;
        sectionLink.textContent = `${section.title}`;
        sectionLink.className = 'card-link'; // Update section link
        sectionTitle.appendChild(sectionLink);
        sectionCard.appendChild(sectionTitle);
        addCopyToClipboard(sectionLink, sectionLink.href);

        // Check for top-level questions in the section
        if (section.questions && section.questions.length > 0) {
            const topLevelCard = document.createElement('div');
            topLevelCard.className = 'faq-rule'; // Reuse the rule styling for consistency

            // Iterate through section-level questions
            section.questions.forEach((qa, index) => {
                const qaCard = document.createElement('div');
                qaCard.className = 'faq-qa';
                qaCard.id = `${sectionCard.id}-qa${index}`; // Generate a unique ID for the Q&A

                // Add link icon to each card
                const linkIcon = document.createElement('a');
                linkIcon.href = `#${qaCard.id}`;
                linkIcon.className = 'link-icon';
                const iconImage = document.createElement('img');
                iconImage.src = 'assets/link_icon.svg';
                iconImage.alt = 'Link';
                linkIcon.appendChild(iconImage);
                qaCard.appendChild(linkIcon);

                const question = document.createElement('p');
                question.className = 'faq-question';
                question.textContent = `Q: ${qa.question}`;

                qaCard.appendChild(question);

                const answer = document.createElement('p');
                answer.className = 'faq-answer';
                answer.textContent = `A: ${qa.answer}`;
                qaCard.appendChild(answer);

                topLevelCard.appendChild(qaCard);

                // Add functionality to copy the link to the clipboard
                addCopyToClipboard(linkIcon, linkIcon.href);
            });

            sectionCard.appendChild(topLevelCard);
        }

        // Iterate through rules in the section
        section.rules.forEach(rule => {
            const ruleCard = document.createElement('div');
            ruleCard.className = 'faq-rule';
            ruleCard.id = `${sectionCard.id}-${sanitizeId(rule.title)}`; // Generate a sanitized ID for the rule

            const ruleTitle = document.createElement('h3');
            const ruleLink = document.createElement('a');
            ruleLink.href = `#${ruleCard.id}`;
            ruleLink.textContent = `${rule.title}`;
            ruleLink.className = 'card-link'; // Update rule link
            ruleTitle.appendChild(ruleLink);
            ruleCard.appendChild(ruleTitle);
            addCopyToClipboard(ruleLink, ruleLink.href);

            // Iterate through questions in the rule
            rule.questions.forEach((qa, index) => {
                const qaCard = document.createElement('div');
                qaCard.className = 'faq-qa';
                qaCard.id = `${ruleCard.id}-qa${index}`; // Generate a unique ID for the Q&A

                // Add link icon to each card
                const linkIcon = document.createElement('a');
                linkIcon.href = `#${qaCard.id}`;
                linkIcon.className = 'link-icon';
                const iconImage = document.createElement('img');
                iconImage.src = 'assets/link_icon.svg';
                iconImage.alt = 'Link';
                linkIcon.appendChild(iconImage);
                qaCard.appendChild(linkIcon);

                const question = document.createElement('p');
                question.className = 'faq-question';
                question.textContent = `Q: ${qa.question}`;
                qaCard.appendChild(question);

                const answer = document.createElement('p');
                answer.className = 'faq-answer';
                answer.textContent = `A: ${qa.answer}`;
                qaCard.appendChild(answer);

                ruleCard.appendChild(qaCard);

                // Add functionality to copy the link to the clipboard
                addCopyToClipboard(linkIcon, linkIcon.href);
            });

            sectionCard.appendChild(ruleCard);
        });

        container.appendChild(sectionCard);
    });

    // Scroll to the element if a hash is present in the URL after rendering
    setTimeout(() => {
        const hash = window.location.hash;
        if (hash) {
            const targetElement = document.querySelector(hash);
            if (targetElement) {
                targetElement.scrollIntoView();
            }
        }
    }, 0); // Delay to ensure rendering is complete

    return container;
}

// Add event listener to copy link to clipboard
function addCopyToClipboard(linkElement, linkUrl) {
    linkElement.addEventListener('click', (event) => {
        navigator.clipboard.writeText(linkUrl).then(() => {
            // Remove any existing 'copied to clipboard' messages
            const existingMessage = document.querySelector('.clipboard-message');
            if (existingMessage) {
                existingMessage.remove();
            }

            // Create and display the 'copied to clipboard' message
            const message = document.createElement('div');
            message.className = 'clipboard-message';
            message.textContent = 'Copied to clipboard';
            document.body.appendChild(message);

            // Position the message near the clicked element
            const rect = linkElement.getBoundingClientRect();
            message.style.position = 'absolute';
            message.style.top = `${rect.top + window.scrollY + 30}px`;
            message.style.left = `${rect.left + window.scrollX}px`;
            message.style.backgroundColor = '#f0f0f0';
            message.style.color = '#333';
            message.style.padding = '5px 10px';
            message.style.borderRadius = '5px';
            message.style.boxShadow = '0 2px 4px rgba(0, 0, 0, 0.1)';
            message.style.fontSize = '12px';
            message.style.zIndex = '1000';

            // Remove the message after 2 seconds
            setTimeout(() => {
                message.remove();
            }, 2000);
        });
    });
}