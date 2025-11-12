document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('participate-form');
    const btnEnviar = document.getElementById('btn-enviar');
    const msgStatus = document.getElementById('mensagemStatus');

    form.addEventListener("submit",async function(event) {
        event.preventDefault();
        
        msgStatus.textContent = "Enviando...";
        msgStatus.className = "status";
        btnEnviar.disabled = true;

        const formData = new FormData(form);

        try {
            const response = await fetch(form.ariaDescription, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                msgStatus.textContent = "Mensagem enviada com sucesso!";
                msgStatus.classList.add("successo");
                form.reset();
            } else {
                msgStatus.textContent = "Erro ao enviar a mensagem. Tente novamente.";
                msgStatus.classList.add("erro");
            }
        } catch (error) {
            console.error('Erro:', error);
            msgStatus.textContent = "Erro ao enviar a mensagem. Tente novamente.";
            msgStatus.classList.add("erro");
        } finally {
            btnEnviar.disabled = false;
        }
    });
});