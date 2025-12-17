(() => {
  "use strict";

  // ---------- Small UI helpers ----------
  function toast(message, type = "info") {
    // type: info | success | error
    const el = document.createElement("div");
    el.className = `toast toast-${type}`;
    el.textContent = message;
    document.body.appendChild(el);

    requestAnimationFrame(() => el.classList.add("show"));
    setTimeout(() => {
      el.classList.remove("show");
      setTimeout(() => el.remove(), 200);
    }, 2200);
  }

  function setStar(button, isFav) {
    // 兼容两种写法：
    // 1) <button class="js-fav-toggle">☆</button>
    // 2) <button ...><span class="js-fav-star">☆</span> 收藏</button>
    const starEl = button.querySelector(".js-fav-star");
    const target = starEl || button;
    target.textContent = isFav ? "★" : "☆";

    button.classList.toggle("is-favorited", isFav);
    button.setAttribute("aria-pressed", String(isFav));
    button.dataset.favorited = isFav ? "1" : "0";
  }

  function getStarState(button) {
    // 优先用 dataset（更可靠）
    if (button.dataset.favorited === "1") return true;
    if (button.dataset.favorited === "0") return false;

    // 再看 DOM 文本
    const starEl = button.querySelector(".js-fav-star");
    const txt = (starEl ? starEl.textContent : button.textContent).trim();
    return txt.includes("★");
  }

  async function toggleFavorite(docId, button) {
    const prev = getStarState(button);
    const next = !prev;

    // 1) Optimistic UI: 先切换
    setStar(button, next);
    button.disabled = true;
    button.classList.add("is-loading");

    try {
      const res = await fetch(`/favorites/toggle/${encodeURIComponent(docId)}`, {
        method: "POST",
        headers: {
          "Accept": "application/json",
          "X-Requested-With": "fetch"
          // 如果你启用了 CSRF：在这里加 X-CSRFToken
        },
        credentials: "same-origin"
      });

      // 2) HTTP 不成功：回滚
      if (!res.ok) {
        setStar(button, prev);
        toast("收藏操作失败，请重试。", "error");
        return;
      }

      // 3) 尝试解析 JSON（推荐后端返回）
      let data = null;
      const ct = res.headers.get("content-type") || "";
      if (ct.includes("application/json")) {
        data = await res.json();
      } else {
        // 有些后端会返回空/HTML：忽略
        try { data = await res.json(); } catch (_) {}
      }

      if (data && typeof data.favorited === "boolean") {
        setStar(button, data.favorited);
        toast(data.favorited ? "已收藏" : "已取消收藏", "success");
      } else {
        // 没有 JSON：就按 optimistic 的结果提示
        toast(next ? "已收藏" : "已取消收藏", "success");
      }
    } catch (e) {
      // 网络异常：回滚
      setStar(button, prev);
      toast("网络错误：无法完成收藏操作。", "error");
    } finally {
      button.disabled = false;
      button.classList.remove("is-loading");
    }
  }

  // ---------- Event delegation ----------
  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".js-fav-toggle");
    if (!btn) return;

    const docId = btn.dataset.docId;
    if (!docId) {
      toast("缺少 doc_id，无法收藏。", "error");
      return;
    }

    toggleFavorite(docId, btn);
  });

  // ---------- Inject minimal toast CSS + favorite states ----------
  // 你也可以把这段挪进 styles.css（但放这里不影响使用）
  const style = document.createElement("style");
  style.textContent = `
    .js-fav-toggle.is-favorited{
      border-color: rgba(154,107,63,.35) !important;
      background: rgba(154,107,63,.14) !important;
    }
    .js-fav-toggle.is-loading{
      opacity: .75;
      cursor: progress;
    }

    .toast{
      position: fixed;
      left: 50%;
      bottom: 20px;
      transform: translateX(-50%) translateY(10px);
      opacity: 0;
      pointer-events: none;
      padding: 10px 14px;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: rgba(253,248,241,.92);
      color: var(--text);
      box-shadow: var(--shadow-sm);
      transition: opacity .18s ease, transform .18s ease;
      font-weight: 750;
      font-size: 13px;
      z-index: 9999;
    }
    .toast.show{
      opacity: 1;
      transform: translateX(-50%) translateY(0);
    }
    .toast-success{
      border-color: rgba(43,182,115,.22);
      background: rgba(43,182,115,.10);
    }
    .toast-error{
      border-color: rgba(181,70,50,.22);
      background: rgba(181,70,50,.10);
    }
  `;
  document.head.appendChild(style);
})();
