(function () {
  const instances = new WeakMap();
  let openInstance = null;
  let uid = 0;

  const textOf = (option) => (option ? option.textContent.trim() : "");
  const normalize = (value) => value.toLowerCase().trim();
  const labelSearch = "\u641c\u7d22\u9009\u9879";
  const labelSelect = "\u8bf7\u9009\u62e9";
  const labelEmpty = "\u672a\u627e\u5230\u5339\u914d\u9009\u9879";

  function positionPopover(instance) {
    if (!instance || instance.popover.hidden || !instance.root.isConnected) return;
    const rect = instance.button.getBoundingClientRect();
    const gap = 8;
    const viewportPadding = 10;
    const width = Math.max(rect.width, 180);
    const left = Math.min(
      Math.max(rect.left, viewportPadding),
      Math.max(viewportPadding, window.innerWidth - width - viewportPadding)
    );

    instance.popover.style.width = `${width}px`;
    instance.popover.style.left = `${left}px`;
    instance.popover.style.top = `${rect.bottom + gap}px`;
    const belowMaxHeight = Math.max(180, window.innerHeight - rect.bottom - gap - viewportPadding);
    instance.popover.style.maxHeight = `${belowMaxHeight}px`;
    instance.list.style.maxHeight = `${Math.max(96, Math.min(268, belowMaxHeight - instance.search.offsetHeight - 23))}px`;

    const popoverRect = instance.popover.getBoundingClientRect();
    if (popoverRect.bottom > window.innerHeight - viewportPadding && rect.top > popoverRect.height + gap) {
      const aboveMaxHeight = Math.max(180, rect.top - gap - viewportPadding);
      instance.popover.style.top = `${Math.max(viewportPadding, rect.top - Math.min(popoverRect.height, aboveMaxHeight) - gap)}px`;
      instance.popover.style.maxHeight = `${aboveMaxHeight}px`;
      instance.list.style.maxHeight = `${Math.max(96, Math.min(268, aboveMaxHeight - instance.search.offsetHeight - 23))}px`;
    }
  }

  function close(instance) {
    if (!instance) return;
    instance.root.classList.remove("is-open");
    instance.popover.hidden = true;
    instance.popover.style.removeProperty("left");
    instance.popover.style.removeProperty("top");
    instance.popover.style.removeProperty("width");
    instance.popover.style.removeProperty("max-height");
    instance.list.style.removeProperty("max-height");
    instance.button.setAttribute("aria-expanded", "false");
    if (openInstance === instance) openInstance = null;
  }

  function closeAll(except = null) {
    document.querySelectorAll(".spotify-select.is-open").forEach((root) => {
      const select = root.previousElementSibling;
      const instance = select ? instances.get(select) : null;
      if (instance && instance !== except) close(instance);
    });
  }

  function getOptions(instance) {
    return Array.from(instance.select.options).filter((option) => !option.disabled);
  }

  function selectedOption(instance) {
    return instance.select.selectedOptions[0] || getOptions(instance)[0] || null;
  }

  function setHighlight(instance, index) {
    const items = Array.from(instance.list.querySelectorAll(".spotify-select__option"));
    if (!items.length) {
      instance.highlightedIndex = -1;
      return;
    }
    const nextIndex = (index + items.length) % items.length;
    items.forEach((item, itemIndex) => {
      item.classList.toggle("is-highlighted", itemIndex === nextIndex);
    });
    instance.highlightedIndex = nextIndex;
    items[nextIndex].scrollIntoView({ block: "nearest" });
  }

  function choose(instance, value) {
    if (instance.select.value === value) {
      close(instance);
      instance.button.focus();
      return;
    }
    close(instance);
    instance.select.value = value;
    instance.select.dispatchEvent(new Event("change", { bubbles: true }));
    if (!instance.root.isConnected) return;
    refresh(instance);
    instance.button.focus();
  }

  function renderList(instance, query = "") {
    const q = normalize(query);
    const options = getOptions(instance);
    const filtered = options.filter((option) => normalize(textOf(option)).includes(q));
    instance.list.innerHTML = "";

    if (!filtered.length) {
      const empty = document.createElement("div");
      empty.className = "spotify-select__empty";
      empty.textContent = labelEmpty;
      instance.list.appendChild(empty);
      instance.highlightedIndex = -1;
      return;
    }

    filtered.forEach((option) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "spotify-select__option";
      item.setAttribute("role", "option");
      item.setAttribute("aria-selected", String(option.selected));
      item.textContent = textOf(option);
      item.dataset.value = option.value;
      if (option.selected) item.classList.add("is-selected");
      item.addEventListener("click", () => choose(instance, option.value));
      instance.list.appendChild(item);
    });

    const selectedIndex = Math.max(0, filtered.findIndex((option) => option.selected));
    setHighlight(instance, selectedIndex);
  }

  function refresh(instance) {
    const current = selectedOption(instance);
    instance.value.textContent = current ? textOf(current) : labelSelect;
    renderList(instance, instance.search.value);
    positionPopover(instance);
  }

  function open(instance) {
    closeAll(instance);
    openInstance = instance;
    instance.root.classList.add("is-open");
    instance.popover.hidden = false;
    instance.button.setAttribute("aria-expanded", "true");
    instance.search.value = "";
    refresh(instance);
    window.requestAnimationFrame(() => {
      positionPopover(instance);
      instance.search.focus({ preventScroll: true });
    });
  }

  function toggle(instance) {
    if (instance.root.classList.contains("is-open")) close(instance);
    else open(instance);
  }

  function enhanceSelect(select) {
    if (instances.has(select) || select.multiple || select.dataset.nativeSelect === "true") return;

    const id = select.id || `spotify-select-${++uid}`;
    select.id = id;

    const root = document.createElement("div");
    root.className = "spotify-select";
    root.dataset.for = id;

    const button = document.createElement("button");
    button.type = "button";
    button.className = "spotify-select__button";
    button.setAttribute("aria-haspopup", "listbox");
    button.setAttribute("aria-expanded", "false");

    const value = document.createElement("span");
    value.className = "spotify-select__value";

    const chevron = document.createElement("span");
    chevron.className = "spotify-select__chevron";
    chevron.setAttribute("aria-hidden", "true");

    const popover = document.createElement("div");
    popover.className = "spotify-select__popover";
    popover.hidden = true;

    const search = document.createElement("input");
    search.type = "search";
    search.className = "spotify-select__search";
    search.placeholder = labelSearch;
    search.autocomplete = "off";

    const list = document.createElement("div");
    list.className = "spotify-select__list";
    list.setAttribute("role", "listbox");
    list.id = `${id}-list`;
    button.setAttribute("aria-controls", list.id);

    button.append(value, chevron);
    popover.append(search, list);
    root.append(button);
    select.classList.add("spotify-native-select");
    select.after(root);
    document.body.append(popover);

    const instance = { select, root, button, value, chevron, popover, search, list, highlightedIndex: -1, refreshFrame: 0 };
    instances.set(select, instance);

    button.addEventListener("click", (event) => {
      event.preventDefault();
      event.stopPropagation();
      toggle(instance);
    });

    button.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open(instance);
      }
    });

    search.addEventListener("input", () => renderList(instance, search.value));
    search.addEventListener("keydown", (event) => {
      if (event.key === "ArrowDown") {
        event.preventDefault();
        setHighlight(instance, instance.highlightedIndex + 1);
      }
      if (event.key === "ArrowUp") {
        event.preventDefault();
        setHighlight(instance, instance.highlightedIndex - 1);
      }
      if (event.key === "Enter") {
        event.preventDefault();
        const item = instance.list.querySelectorAll(".spotify-select__option")[instance.highlightedIndex];
        if (item) choose(instance, item.dataset.value);
      }
      if (event.key === "Escape") {
        event.preventDefault();
        close(instance);
        button.focus();
      }
    });

    select.addEventListener("change", () => refresh(instance));

    const optionObserver = new MutationObserver(() => {
      window.cancelAnimationFrame(instance.refreshFrame);
      instance.refreshFrame = window.requestAnimationFrame(() => refresh(instance));
    });
    optionObserver.observe(select, { childList: true, subtree: true, attributes: true, attributeFilter: ["selected", "label"] });

    refresh(instance);
  }

  function refreshSpotifySelects(root = document) {
    root.querySelectorAll("select").forEach(enhanceSelect);
  }

  document.addEventListener("click", (event) => {
    if (!event.target.closest(".spotify-select, .spotify-select__popover")) closeAll();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") close(openInstance);
  });

  window.addEventListener("scroll", () => positionPopover(openInstance), true);
  window.addEventListener("resize", () => positionPopover(openInstance));

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        if (node.matches?.("select")) enhanceSelect(node);
        refreshSpotifySelects(node);
      });
    });
  });

  window.refreshSpotifySelects = refreshSpotifySelects;
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => refreshSpotifySelects());
  } else {
    refreshSpotifySelects();
  }
  observer.observe(document.documentElement, { childList: true, subtree: true });
})();
