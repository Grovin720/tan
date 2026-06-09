var rule = {
    title: '555电影[V2]', // csp_AppYsV2
    host: 'https://wuwu559.space',
    hostJs: 'print(HOST);let html=request(HOST,{headers:{"User-Agent":PC_UA}});let src=jsp.pdfh(html,".row:eq(2)&&a&&href");print(src);HOST=src+"/api.php/app/"',
    url: 'vodtype/{{tid}}.html',
    filter_url: '&class={{fl.class}}&area={{fl.area}}&lang={{fl.lang}}&letter={{fl.letter}}&year={{fl.year}}&by={{fl.by}}',
    	filter:{
		"1":[{"key":"class","name":"剧情","value":[{"n":"全部","v":""},{"n":"Netflix","v":"Netflix"},{"n":"仙侠","v":"仙侠"},{"n":"剧情","v":"剧情"},{"n":"科幻","v":"科幻"},{"n":"动作","v":"动作"},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"冒险","v":"冒险"},{"n":"儿童","v":"儿童"},{"n":"歌舞","v":"歌舞"},{"n":"音乐","v":"音乐"},{"n":"奇幻","v":"奇幻"},{"n":"动画","v":"动画"},{"n":"恐怖","v":"恐怖"},{"n":"惊悚","v":"惊悚"},{"n":"丧尸","v":"丧尸"},{"n":"战争","v":"战争"},{"n":"传记","v":"传记"},{"n":"纪录","v":"纪录"},{"n":"犯罪","v":"犯罪"},{"n":"悬疑","v":"悬疑"},{"n":"西部","v":"西部"},{"n":"灾难","v":"灾难"},{"n":"古装","v":"古装"},{"n":"武侠","v":"武侠"},{"n":"家庭","v":"家庭"},{"n":"短片","v":"短片"},{"n":"校园","v":"校园"},{"n":"文艺","v":"文艺"},{"n":"运动","v":"运动"},{"n":"青春","v":"青春"},{"n":"同性","v":"同性"},{"n":"励志","v":"励志"},{"n":"人性","v":"人性"},{"n":"美食","v":"美食"},{"n":"女性","v":"女性"},{"n":"治愈","v":"治愈"},{"n":"历史","v":"历史"},{"n":"真人秀","v":"真人秀"},{"n":"脱口秀","v":"脱口秀"}]},{"key":"area","name":"地区","value":[{"n":"全部","v":""},{"n":"大陆","v":"大陆"},{"n":"香港","v":"香港"},{"n":"台湾","v":"台湾"},{"n":"美国","v":"美国"},{"n":"日本","v":"日本"},{"n":"韩国","v":"韩国"},{"n":"英国","v":"英国"},{"n":"法国","v":"法国"},{"n":"德国","v":"德国"},{"n":"印度","v":"印度"},{"n":"泰国","v":"泰国"},{"n":"丹麦","v":"丹麦"},{"n":"瑞典","v":"瑞典"},{"n":"巴西","v":"巴西"},{"n":"加拿大","v":"加拿大"},{"n":"俄罗斯","v":"俄罗斯"},{"n":"意大利","v":"意大利"},{"n":"比利时","v":"比利时"},{"n":"爱尔兰","v":"爱尔兰"},{"n":"西班牙","v":"西班牙"},{"n":"澳大利亚","v":"澳大利亚"}]},{"key":"lang","name":"语言","value":[{"n":"全部","v":""},{"n":"英语","v":"英语"},{"n":"法语","v":"法语"},{"n":"国语","v":"国语"},{"n":"粤语","v":"粤语"},{"n":"日语","v":"日语"},{"n":"韩语","v":"韩语"},{"n":"泰语","v":"泰语"},{"n":"德语","v":"德语"},{"n":"俄语","v":"俄语"},{"n":"闽南语","v":"闽南语"},{"n":"丹麦语","v":"丹麦语"},{"n":"波兰语","v":"波兰语"},{"n":"瑞典语","v":"瑞典语"},{"n":"印地语","v":"印地语"},{"n":"挪威语","v":"挪威语"},{"n":"意大利语","v":"意大利语"},{"n":"西班牙语","v":"西班牙语"}]},{"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"},{"n":"2009","v":"2009"},{"n":"2008","v":"2008"},{"n":"2007","v":"2007"}]}],
		"2":[{"key":"class","name":"剧情","value":[{"n":"全部","v":""},{"n":"Netflix","v":"Netflix"},{"n":"剧情","v":"剧情"},{"n":"丧尸","v":"丧尸"},{"n":"仙侠","v":"仙侠"},{"n":"穿越","v":"穿越"},{"n":"惊悚","v":"惊悚"},{"n":"恐怖","v":"恐怖"},{"n":"言情","v":"言情"},{"n":"科幻","v":"科幻"},{"n":"动作","v":"动作"},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"偶像","v":"偶像"},{"n":"都市","v":"都市"},{"n":"军旅","v":"军旅"},{"n":"谍战","v":"谍战"},{"n":"罪案","v":"罪案"},{"n":"宫廷","v":"宫廷"},{"n":"冒险","v":"冒险"},{"n":"儿童","v":"儿童"},{"n":"歌舞","v":"歌舞"},{"n":"音乐","v":"音乐"},{"n":"奇幻","v":"奇幻"},{"n":"动画","v":"动画"},{"n":"战争","v":"战争"},{"n":"传记","v":"传记"},{"n":"记录","v":"记录"},{"n":"犯罪","v":"犯罪"},{"n":"悬疑","v":"悬疑"},{"n":"西部","v":"西部"},{"n":"灾难","v":"灾难"},{"n":"古装","v":"古装"},{"n":"武侠","v":"武侠"},{"n":"家庭","v":"家庭"},{"n":"短片","v":"短片"},{"n":"校园","v":"校园"},{"n":"文艺","v":"文艺"},{"n":"运动","v":"运动"},{"n":"青春","v":"青春"},{"n":"同性","v":"同性"},{"n":"励志","v":"励志"},{"n":"人性","v":"人性"},{"n":"美食","v":"美食"},{"n":"女性","v":"女性"},{"n":"治愈","v":"治愈"},{"n":"历史","v":"历史"},{"n":"真人秀","v":"真人秀"},{"n":"脱口秀","v":"脱口秀"}]},{"key":"area","name":"地区","value":[{"n":"全部","v":""},{"n":"大陆","v":"大陆"},{"n":"香港","v":"香港"},{"n":"韩国","v":"韩国"},{"n":"美国","v":"美国"},{"n":"日本","v":"日本"},{"n":"法国","v":"法国"},{"n":"英国","v":"英国"},{"n":"德国","v":"德国"},{"n":"台湾","v":"台湾"},{"n":"泰国","v":"泰国"},{"n":"印度","v":"印度"},{"n":"其他","v":"其他"}]},{"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"},{"n":"2009","v":"2009"},{"n":"2008","v":"2008"},{"n":"2007","v":"2007"}]}],
		"3":[{"key":"class","name":"剧情","value":[{"n":"全部","v":""},{"n":"YouTube","v":"YouTube"},{"n":"脱口秀","v":"脱口秀"},{"n":"真人秀","v":"真人秀"},{"n":"选秀","v":"选秀"},{"n":"八卦","v":"八卦"},{"n":"访谈","v":"访谈"},{"n":"情感","v":"情感"},{"n":"生活","v":"生活"},{"n":"晚会","v":"晚会"},{"n":"搞笑","v":"搞笑"},{"n":"音乐","v":"音乐"},{"n":"时尚","v":"时尚"},{"n":"游戏","v":"游戏"},{"n":"少儿","v":"少儿"},{"n":"体育","v":"体育"},{"n":"纪实","v":"纪实"},{"n":"科教","v":"科教"},{"n":"曲艺","v":"曲艺"},{"n":"歌舞","v":"歌舞"},{"n":"财经","v":"财经"},{"n":"汽车","v":"汽车"},{"n":"播报","v":"播报"},{"n":"其他","v":"其他"}]},{"key":"area","name":"地区","value":[{"n":"全部","v":""},{"n":"大陆","v":"大陆"},{"n":"韩国","v":"韩国"},{"n":"香港","v":"香港"},{"n":"台湾","v":"台湾"},{"n":"美国","v":"美国"},{"n":"其它","v":"其它"}]},{"key":"lang","name":"语言","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"其它","v":"其它"}]},{"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"},{"n":"2009","v":"2009"},{"n":"2008","v":"2008"},{"n":"2007","v":"2007"},{"n":"2006","v":"2006"},{"n":"2005","v":"2005"},{"n":"2004","v":"2004"},{"n":"2003","v":"2003"},{"n":"2002","v":"2002"},{"n":"2001","v":"2001"},{"n":"2000","v":"2000"},{"n":"1999","v":"1999"}]}],
		"4":[{"key":"class","name":"剧情","value":[{"n":"全部","v":""},{"n":"Netflix","v":"Netflix"},{"n":"热血","v":"热血"},{"n":"科幻","v":"科幻"},{"n":"美少女","v":"美少女"},{"n":"魔幻","v":"魔幻"},{"n":"经典","v":"经典"},{"n":"励志","v":"励志"},{"n":"少儿","v":"少儿"},{"n":"冒险","v":"冒险"},{"n":"搞笑","v":"搞笑"},{"n":"推理","v":"推理"},{"n":"恋爱","v":"恋爱"},{"n":"治愈","v":"治愈"},{"n":"幻想","v":"幻想"},{"n":"校园","v":"校园"},{"n":"动物","v":"动物"},{"n":"机战","v":"机战"},{"n":"亲子","v":"亲子"},{"n":"儿歌","v":"儿歌"},{"n":"运动","v":"运动"},{"n":"悬疑","v":"悬疑"},{"n":"怪物","v":"怪物"},{"n":"战争","v":"战争"},{"n":"益智","v":"益智"},{"n":"青春","v":"青春"},{"n":"童话","v":"童话"},{"n":"竞技","v":"竞技"},{"n":"动作","v":"动作"},{"n":"社会","v":"社会"},{"n":"友情","v":"友情"},{"n":"真人版","v":"真人版"},{"n":"电影版","v":"电影版"},{"n":"OVA版","v":"OVA版"},{"n":"TV版","v":"TV版"},{"n":"新番动画","v":"新番动画"},{"n":"完结动画","v":"完结动画"}]},{"key":"area","name":"地区","value":[{"n":"全部","v":""},{"n":"大陆","v":"大陆"},{"n":"日本","v":"日本"},{"n":"欧美","v":"欧美"},{"n":"其他","v":"其他"}]},{"key":"lang","name":"语言","value":[{"n":"全部","v":""},{"n":"国语","v":"国语"},{"n":"英语","v":"英语"},{"n":"粤语","v":"粤语"},{"n":"闽南语","v":"闽南语"},{"n":"韩语","v":"韩语"},{"n":"日语","v":"日语"},{"n":"其它","v":"其它"}]},{"key":"year","name":"年份","value":[{"n":"全部","v":""},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"},{"n":"2009","v":"2009"},{"n":"2008","v":"2008"},{"n":"2007","v":"2007"},{"n":"2006","v":"2006"},{"n":"2005","v":"2005"},{"n":"2004","v":"2004"},{"n":"更早","v":"更早"}]}],
"124":[]
	},
    detailUrl: '/voddetail/{{id}}.html',
    searchUrl: '/vodsearch/----------.html?wd={{text}}',
    searchable: 2,
    quickSearch: 0,
    filterable: 1, // 是否启用分类筛选
    headers: {'User-Agent': 'okhttp/4.1.0'},
    timeout: 5000,
    // 分类筛选 /api.php/app/nav || /xgapp.php/v1/nav || /api.php/v1.vod/types
    class_name: '电影&连续剧&动漫&综艺纪录',
    class_url: '1&2&4&3',
    play_parse: true,
    lazy: `js:
        let play_Url = '';
        if (/\\.m3u8|\\.mp4/.test(input)) {
            input = {
                jx: 0,
                url: input,
                parse: 0
            }
        } else if (/,/.test(input) && /url=/.test(input)) {
            input = input.split('url=');
            play_Url = input[0].split(',')[0];
            input = {
                jx: 0,
                url: input[1],
                playUrl: play_Url,
                parse: 1
            }
        } else if (/url=|id=/.test(input)) {
            input = {
                jx: 0,
                url: JSON.parse(request(input)).url,
                parse: 0
            }
        } else if (/youku|iqiyi|v\\.qq\\.com|pptv|sohu|le\\.com|1905\\.com|mgtv|bilibili|ixigua/.test(input)) {
            play_Url = /bilibili/.test(input) ? 'https://jx.xmflv.com/?url=' : 'https://jx.777jiexi.com/player/?url=';
            input = {
                jx: 0,
                url: input,
                playUrl: play_Url,
                parse: 1,
                header: JSON.stringify({
                    'user-agent': 'Mozilla/5.0',
                }),
            }
        } else {
            input
        }
    `,
    limit: 6,
    // 图片来源: '@Referer=https://api.douban.com/@User-Agent=Mozilla/5.0%20(Windows%20NT%2010.0;%20Win64;%20x64)%20AppleWebKit/537.36%20(KHTML,%20like%20Gecko)%20Chrome/113.0.0.0%20Safari/537.36',
    推荐: `js:
        let d = [];
        let jsondata = [];
        let videoList = [];
        if (/vodtype/.test(HOST)) {
            if(HOST.endsWith('/')){
                jsondata = JSON.parse(request(HOST + 'index.php/vod/phb'));
            } else {
                jsondata = JSON.parse(request(HOST + '/index.php/vod/phb'));
            }
            videoList = jsondata.data.list;
        } else {
            jsondata = JSON.parse(request(HOST + '/index.php/vod/index'));
            videoList = jsondata.list;
        }
        videoList.forEach((it,idex) => {
            d.push({
                url: it.id,
                title: it.title,
                img: it.pic,
                desc: it.remarks,
            });
        });
        setResult(d);
    `,
    一级: `js:
        let d = [];
        let jsondata = [];
        let videoList = [];
        if (/vodtype/.test(HOST)) {
            input = HOST + '/index.php/vod/type/id/' + input.split('=')[1] + '.html';
            jsondata = JSON.parse(request(input));
            videoList = jsondata.list;
        } else {
            input = HOST + '/index.php/vod/type/id/' + input.split('=')[1] + '.html';
            jsondata = JSON.parse(request(input));
            videoList = jsondata.list;
        }
        videoList.forEach(it => {
            d.push({
                url: it.id,
                title: it.title,
                img: it.pic,
                desc: it.remarks,
            });
        });
        setResult(d);
    `,
    二级: `js: 
        if (/voddetail/.test(HOST)) {
            input = HOST + '/index.php/vod/detail/id/' + input.split('=')[1] + '.html';
        } else {
            input = HOST + '/index.php/vod/detail/id/' + input.split('=')[1] + '.html';
        }
        try {
            let html = request(input);
            html = JSON.parse(html);
            let node = html.data;
            VOD = {
                vod_id: node.id,
                vod_name: node.title,
                vod_pic: node.pic,
                type_name: node.type,
                vod_year: node.year,
                vod_area: node.area,
                vod_remarks: node.remarks,
                vod_actor: node.actor,
                vod_director: node.director,
                vod_content: node.content.strip()
            };
            var play_url = '';
            var name = {
                'bfzym3u8': '暴风',
                '1080zyk': '优质',
                'kuaikan': '快看',
                'lzm3u8': '量子',
                'ffm3u8': '非凡',
                'snm3u8': '索尼',
                'qhm3u8': '奇虎',
            };
            let episodes = node.play_list;
            if (episodes != '') {
                let playMap = {};
                let arr = [];
                episodes.forEach(ep => {
                    let from = ep.name;
                    if (!playMap.hasOwnProperty(from)) {
                        playMap[from] = []
                    }
                    let parse_api = ep.parse;
                    if (parse_api != null && !/\\.m3u8|\\.mp4/.test(ep.url)) {
                        parse_api = parse_api.replaceAll('..', '.') ;
                        ep.url = ep.url.replaceAll('$', '$' + parse_api);
                    }
                    if (from != null) playMap[from].push(ep.url)
                });
                for (var key in playMap) {
                    arr.push({
                        flag: name[key] ? name[key] : key,
                        url: playMap[key],
                        sort: 8
                    })
                }
                arr.sort((a, b) => a.sort - b.sort);
                let playFrom = [];
                let playList = [];
                arr.map(val => {
                    if (!/undefined/.test(val.flag)) {
                        playFrom.push(val.flag);
                        playList.push(val.url);
                    }
                })
                VOD.vod_play_from = playFrom.join('$$$');
                VOD.vod_play_url = playList.join('$$$');
            } else {
                VOD.vod_play_from = node.play_from;
                VOD.vod_play_url = node.play_url;
            }
        } catch (e) {
            log("获取二级详情页发生错误:" + e.message);
        }
    `,
    搜索: `js:
        let d = [];
        let jsondata = [];
        let videoList = [];
        if (/vodsearch/.test(HOST)) {
            input = HOST + '/index.php/vod/search/wd/' + input.split('=')[1] + '.html';
            jsondata = JSON.parse(request(input));
            videoList = jsondata.list;
        } else {
            input = HOST + '/index.php/vod/search/wd/' + input.split('=')[1] + '.html';
            jsondata = JSON.parse(request(input));
            videoList = jsondata.list;
        }
        videoList.forEach(it => {
            d.push({
                url: it.id,
                title: it.title,
                img: it.pic,
                desc: it.remarks,
            });
        });
        setResult(d);
    `,
}