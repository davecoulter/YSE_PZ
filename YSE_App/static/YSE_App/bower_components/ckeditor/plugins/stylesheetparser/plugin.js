﻿/*
 Copyright (c) 2003-2017, CKSource - Frederico Knabben. All rights reserved.
 For licensing, see LICENSE.md or http://ckeditor.com/license
*/
(function(){function h(b,e,c){var k=[],g=[],a;for(a=0;a<b.styleSheets.length;a++){var d=b.styleSheets[a];if(!((d.ownerNode||d.owningElement).getAttribute("data-cke-temp")||d.href&&"chrome://"==d.href.substr(0,9)))try{for(var f=d.cssRules||d.rules,d=0;d<f.length;d++)g.push(f[d].selectorText)}catch(h){}}a=g.join(" ");a=a.replace(/(,|>|\+|~)/g," ");a=a.replace(/\[[^\]]*/g,"");a=a.replace(/#[^\s]*/g,"");a=a.replace(/\:{1,2}[^\s]*/g,"");a=a.replace(/\s+/g," ");a=a.split(" ");b=[];for(g=0;g<a.length;g++)f=
a[g],c.test(f)&&!e.test(f)&&-1==CKEDITOR.tools.indexOf(b,f)&&b.push(f);for(a=0;a<b.length;a++)c=b[a].split("."),e=c[0].toLowerCase(),c=c[1],k.push({name:e+"."+c,element:e,attributes:{"class":c}});return k}CKEDITOR.plugins.add("stylesheetparser",{init:function(b){b.filter.disable();var e;b.once("stylesSet",function(c){c.cancel();b.once("contentDom",function(){b.getStylesSet(function(c){e=c.concat(h(b.document.$,b.config.stylesheetParser_skipSelectors||/(^body\.|^\.)/i,b.config.stylesheetParser_validSelectors||
/\w+\.\w+/));b.getStylesSet=function(b){if(e)return b(e)};b.fire("stylesSet",{styles:e})})})},null,null,1)}})})();
