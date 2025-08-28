// ==UserScript==
// @name         Figma 中文语言包替换
// @namespace    https://github.com/kailous/figma-zh-CN-localized
// @version      1.0
// @description  自动将 Figma Web 的英文语言包替换为中文
// @author       kailous
// @match        https://www.figma.com/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    // 中文语言包地址（你的 GitHub Pages）
    const zhLangUrl = "https://kailous.github.io/figma-zh-CN-localized/lang/zh.json";

    // 劫持 fetch
    const originalFetch = window.fetch;
    window.fetch = async function(resource, init) {
        try {
            if (typeof resource === "string" &&
                /https:\/\/www\.figma\.com\/webpack-artifacts\/assets\/figma_app-[a-f0-9]{16}\.min\.en\.json\.br/.test(resource)) {
                console.log("[Figma-UserScript] 拦截到英文语言包请求，替换为中文 →", zhLangUrl);
                return originalFetch(zhLangUrl, init);
            }
        } catch (e) {
            console.error("[Figma-UserScript] 替换失败:", e);
        }
        return originalFetch(resource, init);
    };

    // 劫持 XMLHttpRequest（防止有 fallback）
    const origOpen = XMLHttpRequest.prototype.open;
    XMLHttpRequest.prototype.open = function(method, url, ...args) {
        try {
            if (typeof url === "string" &&
                /https:\/\/www\.figma\.com\/webpack-artifacts\/assets\/figma_app-[a-f0-9]{16}\.min\.en\.json\.br/.test(url)) {
                console.log("[Figma-UserScript] XHR 拦截到英文语言包请求，替换为中文 →", zhLangUrl);
                arguments[1] = zhLangUrl;
            }
        } catch (e) {
            console.error("[Figma-UserScript] XHR 替换失败:", e);
        }
        return origOpen.apply(this, arguments);
    };
})();