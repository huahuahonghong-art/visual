/*
(function () {
  /!*const path = location.pathname.replace(/\\/g, "/").toLowerCase();
  const current = path.includes("genre_analysis") ? "module1"
    : path.includes("module2") ? "module2"
      : path.includes("module3") ? "module3"
        : path.includes("module4") ? "module4"
          : path.includes("module5") ? "module5"
            : "home";*!/
            const path = location.pathname.replace(/\\/g, "/").toLowerCase();
let current = "home";
if (path.includes("genre_analysis.html")) current = "module1";
else if (path.includes("module2.html")) current = "module2";
else if (path.includes("module3.html")) current = "module3";
else if (path.includes("module4.html")) current = "module4";
else if (path.includes("module5.html")) current = "module5";
else if (path.includes("recommend.html")) current = "recommend";

  document.body.classList.add("spotify-unified", `spotify-${current}`);

  const root = current === "module1" ? "../../"
    : current === "home" ? "./"
      : "../";

  const links = [
    ["home", "总览", `${root}index.html`],
    ["module1", "模块一 流派画像", `${root}module1/web/genre_analysis.html`],
    ["module2", "模块二 流行度", `${root}moudule2/module2.html`],
    ["module3", "模块三 艺术家", `${root}module3and4/module3.html`],
    ["module4", "模块四 情绪空间", `${root}module3and4/module4.html`],
    ["module5", "模块五 特征关联", `${root}module5/module5.html`],
  ];

  const nav = document.createElement("nav");
  nav.className = "spotify-site-nav";
  nav.innerHTML = `
    <a class="spotify-site-brand" href="${root}index.html">音律图谱 · Spotify Rhythm Atlas</a>
    <div class="spotify-site-links">
      ${links.map(([key, label, href]) => `<a class="${current === key ? "active" : ""}" href="${href}">${label}</a>`).join("")}
    </div>
  `;
  document.body.prepend(nav);

  const recommendEntry = document.createElement("a");
  recommendEntry.className = `spotify-recommend-entry${current === "recommend" ? " active" : ""}`;
  recommendEntry.href = `${root}recommend/recommend.html`;
  recommendEntry.setAttribute("aria-label", "推荐几首");
  recommendEntry.innerHTML = `
    <span class="spotify-recommend-mascot" aria-hidden="true">
      <img src="${root}shared/recommend-icon.png" alt="">
    </span>
    <span class="spotify-recommend-text">推荐几首</span>
  `;
  document.body.append(recommendEntry);
})();
*/
(function () {
  const path = location.pathname.replace(/\\/g, "/").toLowerCase();
  let current = "module1";
  if (path.includes("genre_analysis.html")) current = "module1";
  else if (path.includes("module2.html")) current = "module2";
  else if (path.includes("module3.html")) current = "module3";
  else if (path.includes("module4.html")) current = "module4";
  else if (path.includes("module5.html")) current = "module5";
  else if (path.includes("recommend.html")) current = "recommend";

  document.body.classList.add("spotify-unified", `spotify-${current}`);

  const root = current === "module1" ? "../../"
      : "../";

  // 已彻底移除总览home条目，保留你的 moudule2 原名
  const links = [
    ["module1", "模块一 流派画像", `${root}module1/web/genre_analysis.html`],
    ["module2", "模块二 流行度", `${root}moudule2/module2.html`],
    ["module3", "模块三 艺术家", `${root}module3and4/module3.html`],
    ["module4", "模块四 情绪空间", `${root}module3and4/module4.html`],
    ["module5", "模块五 特征关联", `${root}module5/module5.html`],
  ];

  const nav = document.createElement("nav");
  nav.className = "spotify-site-nav";
  nav.innerHTML = `
    <a class="spotify-site-brand" href="${root}module1/web/genre_analysis.html">音律图谱 · Spotify Rhythm Atlas</a>
    <div class="spotify-site-links">
      ${links.map(([key, label, href]) => `<a class="${current === key ? "active" : ""}" href="${href}">${label}</a>`).join("")}
    </div>
  `;
  document.body.prepend(nav);

  const recommendEntry = document.createElement("a");
  recommendEntry.className = `spotify-recommend-entry${current === "recommend" ? " active" : ""}`;
  recommendEntry.href = `${root}recommend/recommend.html`;
  recommendEntry.setAttribute("aria-label", "推荐几首");
  recommendEntry.innerHTML = `
    <span class="spotify-recommend-mascot" aria-hidden="true">
      <img src="${root}shared/recommend-icon.png" alt="">
    </span>
    <span class="spotify-recommend-text">推荐几首</span>
  `;
  document.body.append(recommendEntry);
})();