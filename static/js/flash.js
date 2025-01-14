
  document.addEventListener("DOMContentLoaded", function() {
    const flashMessages = document.querySelectorAll(".flash-popup");

    // Hapus flash message setelah 4 detik
    flashMessages.forEach((msg) => {
      setTimeout(() => {
        msg.style.display = "none";
      }, 4000);
    });
  });

