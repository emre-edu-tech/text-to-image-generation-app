const form = document.getElementById("generate-form");
const promptInput = document.getElementById("prompt");
const loading = document.getElementById("loading");
const resultImg = document.getElementById("result-img");
const downloadLink = document.getElementById("download-link");
const errorBox = document.getElementById("error-box");

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) return;

  errorBox.classList.add("hidden");
  resultImg.classList.add("hidden");
  downloadLink.classList.add("hidden");
  loading.classList.remove("hidden");

  try {
    const res = await fetch("/api/generate-image", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || "Image generation failed");
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    resultImg.src = url;
    resultImg.classList.remove("hidden");
    downloadLink.href = url;
    downloadLink.classList.remove("hidden");
  } catch (err) {
    errorBox.textContent = err.message;
    errorBox.classList.remove("hidden");
  } finally {
    loading.classList.add("hidden");
  }
});
