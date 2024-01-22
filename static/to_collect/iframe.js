/*
 * insérer le tag scrit suivant dans la div qui affichera l'iframe
 * <script id="lvao_iframe" src="https://longuevieauxobjets.ademe.fr/iframe_client.js" data-params="{}"></script>
 *
 * le code ci-dessous permet d'ajouter l'iframe dans la page
 */
// Add iframeResizer.min.js to the head
var head = document.head;
var script1 = document.createElement("script");
script1.src =
    "https://cdnjs.cloudflare.com/ajax/libs/iframe-resizer/4.3.6/iframeResizer.min.js";
script1.integrity =
    "sha512-f0wd6UIvZbsjPNebGx+uMzHmg6KXr1jWvumJDYSEDmwYJYOptZ0dTka/wBJu7Tj80tnCYMKoKicqvZiIc9GJgw==";
script1.crossOrigin = "anonymous";
script1.referrerPolicy = "no-referrer";
head.appendChild(script1);
// Add iFrame just after the script tag
var scriptTag = document.getElementById("lvao_script");
var urlParams = scriptTag.dataset.params
    ? new URLSearchParams(JSON.parse(scriptTag.dataset.params))
    : new URLSearchParams();
urlParams.append("iframe", "1");
var baseUrl = "https://longuevieauxobjets.ademe.fr";
var iframe = document.createElement("iframe");
iframe.src = "".concat(baseUrl, "?").concat(urlParams.toString());
iframe.id = "lvao_iframe";
iframe.setAttribute("frameborder", "0");
iframe.setAttribute("scrolling", "no");
iframe.setAttribute("allow", "geolocation");
iframe.style.width = "100%";
scriptTag.insertAdjacentElement("afterend", iframe);
// Add iFrameResize script to the end of the body
var body = document.body;
var script2 = document.createElement("script");
script2.textContent = "\n    document.getElementById('lvao_iframe').addEventListener('load', function () {\n        iFrameResize({\n            heightCalculationMethod: 'bodyScroll',\n            maxWidth: 800,\n        }, '#lvao_iframe')\n    });\n";
body.appendChild(script2);
