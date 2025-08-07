// Copy webhook URL functionality for Django admin
function copyToClipboard(elementId) {
    const input = document.getElementById(elementId);
    if (input) {
        input.select();
        input.setSelectionRange(0, 99999); // For mobile devices
        
        navigator.clipboard.writeText(input.value).then(function() {
            // Find the button next to this input
            const button = input.nextElementSibling;
            if (button) {
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                button.style.backgroundColor = '#28a745';
                button.style.color = 'white';
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.backgroundColor = '';
                    button.style.color = '';
                }, 2000);
            }
        }).catch(function(err) {
            console.error('Could not copy text: ', err);
            // Fallback for older browsers
            document.execCommand('copy');
        });
    }
}
