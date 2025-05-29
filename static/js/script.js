let currentFile = null;
let selectedSemitones = 0;

document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("audioFile");
    const player = document.getElementById("audioPlayer");
    const audioSection = document.getElementById("audio-section");
    const toneValue = document.getElementById("toneValue");
    const progressBar = document.getElementById("uploadProgress");
    const progressContainer = document.getElementById("progressContainer");
    const fileNameDisplay = document.getElementById("fileName");
    const transposingStatus = document.getElementById("transposingStatus");
    const transposeButton = document.getElementById("transposeButton");
    const uploadLabel = document.querySelector(".upload-label");
    const toneButtons = document.querySelectorAll(".btn-transpose");

    // Drag and drop functionality
    uploadLabel.addEventListener("dragover", function(e) {
        e.preventDefault();
        uploadLabel.classList.add("border-primary");
    });

    uploadLabel.addEventListener("dragleave", function() {
        uploadLabel.classList.remove("border-primary");
    });

    uploadLabel.addEventListener("drop", function(e) {
        e.preventDefault();
        uploadLabel.classList.remove("border-primary");

        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            handleFileUpload(e.dataTransfer.files[0]);
        }


    });

    // Upload com barra de progresso
    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]);
        }
    });



    function handleFileUpload(file) {
        if (!file) return;

        // Exibe nome do arquivo com ícone
        fileNameDisplay.innerHTML = `<i class="fas fa-file-audio text-primary me-1"></i> ${file.name}`;

        const formData = new FormData();
        formData.append("file", file);

        // Debugando o FormData (mostrar no console do navegador)
        console.log("Enviando arquivo:", file.name, "Tamanho:", file.size, "Tipo:", file.type);

        const xhr = new XMLHttpRequest();

        progressContainer.style.display = "block";
        progressBar.style.width = "0%";
        progressBar.innerText = "0%";

        xhr.upload.addEventListener("progress", function (e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                progressBar.style.width = `${percent}%`;
                progressBar.innerText = `${percent}%`;
            }
        });

        xhr.onload = function () {
            console.log("Status da resposta:", xhr.status);
            console.log("Resposta recebida:", xhr.responseText);

            if (xhr.status === 200) {
    try {
        const data = JSON.parse(xhr.responseText);
        // ✅ Salvar nome do arquivo no localStorage
        let enviados = JSON.parse(localStorage.getItem("arquivosEnviados") || "[]");
        const baseName = getBaseFilename(data.filename);

        if (!enviados.includes(baseName)) {
            enviados.push(baseName);
            localStorage.setItem("arquivosEnviados", JSON.stringify(enviados));
        }



        // 🟢 Atualiza o tom original na interface
        const originalKeyEl = document.getElementById("originalKey");
        if (originalKeyEl) {
            originalKeyEl.innerText = data.original_key.full_key;
        }

        player.src = data.url;
        player.load();
        player.play();

        audioSection.style.display = "block";
        progressContainer.style.display = "none";
        currentFile = data.filename;
        const tonesDownContainer = document.getElementById("tonesDown");
const tonesUpContainer = document.getElementById("tonesUp");

// Limpa os botões anteriores
tonesDownContainer.innerHTML = "";
tonesUpContainer.innerHTML = "";

// Botão para o tom original
const originalBtn = document.createElement("button");
originalBtn.className = "btn btn-outline-primary btn-sm mx-1 my-1 btn-transpose active";
originalBtn.dataset.semitones = "0";
originalBtn.innerText = "Tom Original";
tonesDownContainer.appendChild(originalBtn);

// Evento do botão original
originalBtn.addEventListener("click", function () {
    document.querySelectorAll(".btn-transpose").forEach(btn => btn.classList.remove("active"));
    originalBtn.classList.add("active");
    selectedSemitones = 0;
    toneValue.innerText = "0";

    const selectedKeyText = document.getElementById("selectedKeyText");
    if (selectedKeyText) {
        selectedKeyText.innerText = "tom original";
    }

    // Recarrega o áudio original
    if (player && data.url) {
        player.src = data.url;
        player.load();
        player.play();
    }
});


// Renderiza os botões dinamicamente
data.available_keys.forEach(key => {
    const button = document.createElement("button");
    button.className = "btn btn-outline-secondary btn-sm mx-1 my-1 btn-transpose";
    button.dataset.semitones = key.semitones;
    button.innerText = key.key_name;

    // Adiciona ao container certo
    if (key.direction === "abaixo") {
        tonesDownContainer.appendChild(button);
    } else {
        tonesUpContainer.appendChild(button);
    }

    // Evento de clique
    button.addEventListener("click", function () {
        // Remover 'active' de todos os botões
        document.querySelectorAll(".btn-transpose").forEach(btn => btn.classList.remove("active"));

        // Ativar o botão clicado
        button.classList.add("active");

        // Atualizar semitons e exibição
        selectedSemitones = parseInt(button.dataset.semitones);
        toneValue.innerText = selectedSemitones > 0 ? `+${selectedSemitones}` : selectedSemitones;

        const selectedKeyText = document.getElementById("selectedKeyText");
        if (selectedKeyText) {
            selectedKeyText.innerText = button.innerText;
        }
    });
});


        // Ativar botão de transposição
        transposeButton.disabled = false;

        // Reset semitones selection
        resetSemitonesSelection();
    } catch (parseError) {
        console.error("Erro ao processar resposta:", parseError);
        showAlert("Erro ao processar resposta do servidor", "danger");
    }
}
 else {
                let errorMsg = "Erro ao enviar o áudio.";
                try {
                    const errorData = JSON.parse(xhr.responseText);
                    errorMsg = errorData.error || errorMsg;
                } catch (e) {}

                showAlert(errorMsg, "danger");
                progressContainer.style.display = "none";
            }
        };

        xhr.onerror = function (e) {
            console.error("Erro na requisição:", e);
            showAlert("Erro de conexão com o servidor.", "danger");
            progressContainer.style.display = "none";
        };

        xhr.open("POST", "/upload-audio");
        xhr.send(formData);
    }

    // Botões de seleção de semitons
    toneButtons.forEach(button => {
        button.addEventListener("click", function() {
            // Remover classe ativa de todos os botões
            toneButtons.forEach(btn => btn.classList.remove("active"));

            // Adicionar classe ativa ao botão clicado
            this.classList.add("active");

            // Atualizar o valor de semitons selecionado
            selectedSemitones = parseInt(this.dataset.semitones);
            toneValue.innerText = selectedSemitones > 0 ? `+${selectedSemitones}` : selectedSemitones;
        });
    });

    // Função para resetar a seleção de semitons
    function resetSemitonesSelection() {
        selectedSemitones = 0;
        toneValue.innerText = "0";
        toneButtons.forEach(btn => {
            btn.classList.remove("active");
            if (btn.dataset.semitones === "0") {
                btn.classList.add("active");
            }
        });
    }

    // Botão de transposição
transposeButton.addEventListener("click", async function () {
    if (!currentFile) return;

    transposingStatus.style.display = "block";
    transposeButton.disabled = true;

    try {
        const response = await fetch("/transpose", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                filename: currentFile,
                semitones: selectedSemitones,
            }),
        });

        if (!response.ok) {
            throw new Error("Erro na resposta do servidor");
        }

        const data = await response.json();
        player.src = data.url;
        player.load();
        player.play();

        showAlert(`Áudio transposto em ${selectedSemitones} semitons com sucesso!`, "success");

        // 🔽 Mostrar botão de download com texto personalizado
        const downloadContainer = document.getElementById("downloadContainer");
        const downloadButton = document.getElementById("downloadButton");

        if (downloadContainer && downloadButton) {
            downloadButton.href = data.download_url;
            downloadButton.download = `audio_transposto_${selectedSemitones >= 0 ? '+' : ''}${selectedSemitones}.mp3`;

            // 📝 Texto do botão
            let textoBotao = "Baixar áudio no tom ";
            if (selectedSemitones === 0 || data.new_key.toLowerCase().includes("original")) {
                textoBotao += "(tom original)";
            } else {
                textoBotao += `(${data.new_key})`;
            }
            downloadButton.innerText = textoBotao;

            downloadContainer.style.display = "block";
        }

        // Atualiza "Tom Atual"
        const currentKey = document.getElementById("currentKey");
        const currentKeyContainer = document.getElementById("currentKeyContainer");
        if (currentKey && currentKeyContainer) {
            currentKey.innerText = data.new_key;
            currentKeyContainer.style.display = "block";
        }

    } catch (err) {
        showAlert("Erro ao transpor o áudio.", "danger");
    } finally {
        transposingStatus.style.display = "none";
        transposeButton.disabled = false;
    }
});



    // Função para exibir alertas
    function showAlert(message, type) {
        // Criar elemento de alerta
        const alertElement = document.createElement("div");
        alertElement.className = `alert alert-${type} alert-dismissible fade show mt-3`;
        alertElement.role = "alert";
        alertElement.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;

        // Inserir antes do fim da seção de áudio
        const audioSection = document.getElementById("audio-section");
        audioSection.insertAdjacentElement('beforeend', alertElement);

        // Auto-remover após 5 segundos
        setTimeout(() => {
            alertElement.classList.remove("show");
            setTimeout(() => alertElement.remove(), 300);
        }, 5000);
    }


function atualizarHistorico() {
    fetch('/historico')
        .then(res => res.json())
        .then(data => renderHistorico(data))
        .catch(err => console.error("Erro ao atualizar histórico:", err));
}


function nomeLimpo(filename) {
    return filename
        .replace(/^\d+_/, '')           // remove timestamp
        .replace(/_/g, ' ')             // troca _ por espaço
        .replace(/\.\w+$/, '');         // remove extensão
}


function getBaseFilename(fullFilename) {
    return fullFilename.replace(/^\d+_/, ''); // remove o timestamp do início
}


    // Carrega histórico de músicas processadas
fetch('/historico')
    .then(res => res.json())
    .then(data => renderHistorico(data))
    .catch(err => console.error("Erro ao carregar histórico:", err));

function renderHistorico(musicas) {
    const container = document.getElementById("historyAccordion");
    if (!container) return;

    container.innerHTML = "";

    const enviados = JSON.parse(localStorage.getItem("arquivosEnviados") || "[]");

    // 🎯 Agrupa por nome base, guardando apenas a versão mais recente
    const agrupadas = {};
    musicas.forEach(m => {
        const base = getBaseFilename(m.filename);
        if (enviados.includes(base)) {
            if (!agrupadas[base] || m.timestamp > agrupadas[base].timestamp) {
                agrupadas[base] = m;
            }
        }
    });

    const unicos = Object.values(agrupadas);

    if (unicos.length === 0) {
        container.innerHTML = `<div class="alert alert-info">Nenhum histórico desta sessão ainda.</div>`;
        return;
    }

    // 📦 Renderiza os arquivos únicos
    unicos.forEach((musica, index) => {
        const collapseId = `collapse-${index}`;
        const item = document.createElement("div");
        item.className = "accordion-item mb-2";

        item.innerHTML = `
            <h2 class="accordion-header" id="heading-${index}">
                <button class="accordion-button collapsed" type="button"
                    data-bs-toggle="collapse" data-bs-target="#${collapseId}" aria-expanded="false"
                    aria-controls="${collapseId}">
                    🎵 ${nomeLimpo(musica.filename)}
                    <span class="ms-auto text-muted small">Tom original: ${musica.original_key}</span>
                </button>
            </h2>
            <div id="${collapseId}" class="accordion-collapse collapse"
                aria-labelledby="heading-${index}" data-bs-parent="#historyAccordion">
                <div class="accordion-body">
                    <p class="mb-2"><strong>Tom original:</strong> ${musica.original_key}</p>
                    <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-3">
                        ${musica.available_keys
                            .filter(key => key.processed)
                            .map(key => `
                                <div class="col">
                                    <div class="border p-3 rounded bg-light h-100 d-flex flex-column justify-content-between">
                                        <div class="fw-semibold mb-2 text-center">${key.key_name}</div>
                                        <audio controls preload="none" src="/static/processed/transposed_${key.semitones}_${musica.filename}" style="width: 100%; max-width: 100%;"></audio>
                                        <a class="btn btn-sm btn-outline-success mt-2" href="/static/processed/transposed_${key.semitones}_${musica.filename}" download>
                                            <i class="fas fa-download me-1"></i> Baixar
                                        </a>
                                    </div>
                                </div>
                            `).join('')}
                    </div>
                </div>
            </div>
        `;

        container.appendChild(item);
    });
}


});