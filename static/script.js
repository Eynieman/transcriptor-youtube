function copiarTexto() {
    var texto = document.getElementById("texto-transcripcion").innerText;
    navigator.clipboard.writeText(texto).then(function() {
        var aviso = document.getElementById("aviso-copiado");
        aviso.style.display = "inline";
        setTimeout(function() { aviso.style.display = "none"; }, 2000);
    });
}

function copiarTabla() {
    var filas = document.querySelectorAll("#tabla-transcripcion tr");
    var texto = "";
    filas.forEach(function(fila) {
        var celdas = fila.querySelectorAll("td");
        texto += "[" + celdas[0].innerText + "] " + celdas[1].innerText + "\n";
    });
    navigator.clipboard.writeText(texto).then(function() {
        var aviso = document.getElementById("aviso-copiado2");
        aviso.style.display = "inline";
        setTimeout(function() { aviso.style.display = "none"; }, 2000);
    });
}

function descargarTexto() {
    var texto = document.getElementById("texto-transcripcion").innerText;
    var blob = new Blob([texto], { type: "text/plain" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "transcripcion.txt";
    a.click();
}

function descargarTabla() {
    var filas = document.querySelectorAll("#tabla-transcripcion tr");
    var texto = "";
    filas.forEach(function(fila) {
        var celdas = fila.querySelectorAll("td");
        texto += "[" + celdas[0].innerText + "] " + celdas[1].innerText + "\n";
    });
    var blob = new Blob([texto], { type: "text/plain" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "transcripcion_timestamps.txt";
    a.click();
}

function copiarResumen() {
    var texto = document.getElementById("texto-resumen").innerText;
    navigator.clipboard.writeText(texto).then(function() {
        var aviso = document.getElementById("aviso-copiado3");
        aviso.style.display = "inline";
        setTimeout(function() { aviso.style.display = "none"; }, 2000);
    });
}

function descargarResumen() {
    var texto = document.getElementById("texto-resumen").innerText;
    var blob = new Blob([texto], { type: "text/plain" });
    var a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "resumen.txt";
    a.click();
}

function resumir() {
    var texto = document.getElementById("texto-transcripcion").innerText;
    var bloqueResumen = document.getElementById("bloque-resumen");
    var textoResumen = document.getElementById("texto-resumen");

    textoResumen.innerText = "Generando resumen...";
    bloqueResumen.style.display = "block";

    fetch("/resumir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transcripcion: texto })
    })
    .then(function(response) { return response.json(); })
    .then(function(data) {
        if (data.error) {
            textoResumen.innerText = "Error: " + data.error;
        } else {
            textoResumen.innerHTML = data.resumen
                .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                .replace(/\n/g, "<br>");
        }
    })
    .catch(function() {
        textoResumen.innerText = "Error al conectar con el servidor.";
    });
}

function cambiarModo() {
    var modo = document.querySelector('input[name="modo"]:checked').value;
    var bloqueTexto = document.getElementById("bloque-texto");
    var bloqueTabla = document.getElementById("bloque-tabla");
    if (bloqueTexto) bloqueTexto.style.display = (modo === "texto") ? "block" : "none";
    if (bloqueTabla) bloqueTabla.style.display = (modo === "timestamps") ? "block" : "none";
}

document.addEventListener("DOMContentLoaded", function() {
    var radios = document.querySelectorAll('input[name="modo"]');
    radios.forEach(function(radio) {
        radio.addEventListener("change", cambiarModo);
    });
    cambiarModo();
});
