// 央视大全HD —— 央视栏目大全点播 (tv.cctv.com/lm/)
// 分类: 主页 + CCTV-1~17 / CCTV-5+ / CCTV-16奥林匹克 (cid 用官方 EPGC 频道ID, 精确过滤, 支持翻页)
// 栏目选集: 最新一期 guid -> videoinfoByGuid 取 ctid (即 TOPC 编号) -> getVideoListByColumn 按日期倒序
// 清晰度: hls_url 的 main.m3u8 只含 480x270 一档, 换成 /2000/2000.m3u8 得 2000kbps 超清流
var rule = {
    title: '央视大全',
    CID_MAP: {
        '主页': '',
        'CCTV-1综合': 'EPGC1386744804340101',
        'CCTV-2财经': 'EPGC1386744804340102',
        'CCTV-3综艺': 'EPGC1386744804340103',
        'CCTV-4中文国际': 'EPGC1386744804340104',
        'CCTV-5体育': 'EPGC1386744804340107',
        'CCTV-5+体育赛事': 'EPGC1468294755566101',
        'CCTV-6电影': 'EPGC1386744804340108',
        'CCTV-7国防军事': 'EPGC1386744804340109',
        'CCTV-8电视剧': 'EPGC1386744804340110',
        'CCTV-9纪录': 'EPGC1386744804340112',
        'CCTV-10科教': 'EPGC1386744804340113',
        'CCTV-11戏曲': 'EPGC1386744804340114',
        'CCTV-12社会与法': 'EPGC1386744804340115',
        'CCTV-13新闻': 'EPGC1386744804340116',
        'CCTV-14少儿': 'EPGC1386744804340117',
        'CCTV-15音乐': 'EPGC1386744804340118',
        'CCTV-16奥林匹克': 'EPGC1634630207058998',
        'CCTV-17农业农村': 'EPGC1563932742616872'
    },
    host: 'https://tv.cctv.com',
    homeUrl: '',
    推荐: '',
    url: '',
    searchable: 0,
    quickSearch: 0,
    filterable: 0,
    multi: 1,
    limit: 20,
    timeout: 10000,
    headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://tv.cctv.com/'
    },
    class_name: '主页&CCTV-1综合&CCTV-2财经&CCTV-3综艺&CCTV-4中文国际&CCTV-5体育&CCTV-5+体育赛事&CCTV-6电影&CCTV-7国防军事&CCTV-8电视剧&CCTV-9纪录&CCTV-10科教&CCTV-11戏曲&CCTV-12社会与法&CCTV-13新闻&CCTV-14少儿&CCTV-15音乐&CCTV-16奥林匹克&CCTV-17农业农村',
    class_url: '主页&CCTV-1综合&CCTV-2财经&CCTV-3综艺&CCTV-4中文国际&CCTV-5体育&CCTV-5+体育赛事&CCTV-6电影&CCTV-7国防军事&CCTV-8电视剧&CCTV-9纪录&CCTV-10科教&CCTV-11戏曲&CCTV-12社会与法&CCTV-13新闻&CCTV-14少儿&CCTV-15音乐&CCTV-16奥林匹克&CCTV-17农业农村',
    play_parse: true,
    lazy: $js.toString(() => {
        // input = 视频guid -> 解析真实高清播放地址 (强制 2000kbps 档)
        try {
            let api = 'https://vdn.apps.cntv.cn/api/getHttpVideoInfo.do?pid=' + input;
            let html = request(api);
            let j = JSON.parse(html);
            let hls = (j.hls_url || '').trim();
            let hd = hls.replace('/main/', '/2000/').replace('main.m3u8', '2000.m3u8');
            input = {
                parse: 0,
                url: hd || hls,
                jx: 0,
                header: {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://tv.cctv.com/'
                }
            };
        } catch (e) {
            input = { parse: 0, url: input, jx: 0 };
        }
    }),
    一级: $js.toString(() => {
        // 栏目列表: columnSearch 用 cid(官方EPGC频道ID) 精确过滤, 支持翻页
        let d = [];
        let html = '';
        try {
            let cate = (MY_CATE || '').trim();
            let page = MY_PAGE || 1;
            if (cate === '主页' && page > 5) { setResult(d); return; }
            let cid = rule.CID_MAP[cate] || '';
            // 主路径: 用官方频道 cid 精确过滤
            let url = 'https://api.cntv.cn/lanmu/columnSearch?&fl=&fc=&cid=' + cid + '&p=' + page + '&n=20&serviceId=tvcctv&t=json&cb=ko';
            html = request(url) || '';
            log('[央视大全][一级] cate=' + cate + ' cid=' + cid + ' page=' + page + ' 响应长度=' + html.length);
            // 剥 JSONP 外壳 ko(...) 或纯 JSON
            let s = html.trim();
            if (s.startsWith('ko(')) s = s.slice(3);
            if (s.endsWith(');')) s = s.slice(0, -2);
            else if (s.endsWith(')')) s = s.slice(0, -1);
            let j = JSON.parse(s);
            let docs = (j.response && j.response.docs) || [];
            // 兜底: cid 无效或为空(如 MY_CATE 没匹配上)时, 退回用频道名搜索
            if (!docs.length && cate && cate !== '主页') {
                let u2 = 'https://api.cntv.cn/lanmu/columnSearch?&fl=&fc=&channel_name=' + encodeURIComponent(cate) + '&p=' + page + '&n=20&serviceId=tvcctv&t=json&cb=ko';
                let h2 = request(u2) || '';
                log('[央视大全][一级] 兜底频道名搜索 响应长度=' + h2.length);
                let s2 = h2.trim();
                if (s2.startsWith('ko(')) s2 = s2.slice(3);
                if (s2.endsWith(');')) s2 = s2.slice(0, -2);
                else if (s2.endsWith(')')) s2 = s2.slice(0, -1);
                let j2 = JSON.parse(s2);
                docs = (j2.response && j2.response.docs) || [];
            }
            let seen = {};
            docs.forEach(function (it) {
                let key = it.column_id || it.column_name;
                if (seen[key]) return;
                seen[key] = 1;
                d.push({
                    title: it.column_name || '',
                    img: it.column_logo || '',
                    desc: (it.channel_name || '') + (it.column_playdate ? ' | ' + it.column_playdate : ''),
                    url: (it.column_name || '') + '||' + (it.column_website || '') + '||' + (it.column_id || '') + '||' + ((it.lastVIDE && it.lastVIDE.videoSharedCode) || '')
                });
            });
            if (!d.length) log('[央视大全][一级] 空数据, raw前600字=' + html.slice(0, 600));
        } catch (e) {
            log('[央视大全][一级] 出错: ' + e.message + ' | raw前600字=' + html.slice(0, 600));
        }
        setResult(d);
    }),
    二级: $js.toString(() => {
        // input = 栏目名||栏目页||column_id||最新一期guid
        // 主路径: guid -> videoinfoByGuid 取 ctid(即TOPC编号) -> getVideoListByColumn 拉选集
        // 兜底: 抓栏目页 HTML 正则 TOPC
        VOD = {};
        let d = [];
        let parts = input.split('||');
        let vname = parts[0] || '央视栏目';
        let website = parts[1] || '';
        let columnId = parts[2] || '';
        let lastGuid = parts[3] || '';
        VOD = {
            vod_name: vname,
            vod_pic: '',
            vod_content: vname + ' - 央视高清回看(2000kbps)',
            vod_play_from: '央视超清'
        };
        try {
            let topc = '';
            // 主路径: ctid
            if (lastGuid) {
                try {
                    let info = JSON.parse(request('https://api.cntv.cn/video/videoinfoByGuid?guid=' + lastGuid + '&serviceId=tvcctv'));
                    if (info && info.ctid && /^TOPC\d+$/.test(info.ctid)) topc = info.ctid;
                } catch (e) { }
            }
            // 兜底: 抓栏目页
            if (!topc && website) {
                try {
                    let m = request(website).match(/TOPC[0-9]+/);
                    if (m) topc = m[0];
                } catch (e) { }
            }
            if (topc) {
                for (let p = 1; p <= 2; p++) {
                    let u = 'https://api.cntv.cn/NewVideo/getVideoListByColumn?id=' + topc + '&n=100&sort=desc&p=' + p + '&mode=0&serviceId=tvcctv';
                    let j = JSON.parse(request(u));
                    let lst = (j.data && j.data.list) || [];
                    lst.forEach(function (v) {
                        if (v.guid) d.push({ title: (v.title || '').trim(), url: v.guid });
                    });
                    if (lst.length < 100) break;
                }
            }
            if (d.length === 0 && lastGuid) {
                d.push({ title: vname + ' 最新一期', url: lastGuid });
            }
            let seen = {};
            d = d.filter(function (it) {
                if (seen[it.title]) return false;
                seen[it.title] = 1;
                return true;
            });
            VOD.vod_play_url = d.map(function (it) { return it.title + '$' + it.url; }).join('#');
        } catch (e) {
            log('cctv_hd 二级出错: ' + e.message);
            VOD.vod_play_url = lastGuid ? (vname + ' 最新一期$' + lastGuid) : '加载失败$error';
        }
        setResult(d);
    })
};
