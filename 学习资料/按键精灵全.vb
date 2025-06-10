
/*------------------------------------------------------------------------------------------*/
/*----------------------------注意事项（必看！！！！！！！）----------------------------------*/
/*------------------------------------------------------------------------------------------*/


//模拟器需要1920*1080！
//游戏设置：关闭“继承交替情报”，视野“标准”，“探索”里关闭“任务追踪”。
//注意战斗开始时尽量不要让buff挡住角色状态栏，避免脚本识别错误。如果莫名出现总是自动回复状态的情况，很可能是这个原因，可以自行前往脚本1069行，延长delay时间
//运行脚本前需要看脚本“功能设置”。怎么改设置都写了，如我想要用叹息冰窟刷怪，就在“设置刷怪地点”里找到“//txbk”，改成“txbk”即可
//请打开游戏界面之后再运行脚本，以确保获取正确的游戏包名（如果手动修改了游戏包名就不需要了）
//交流群群号213459239

/*-----------------------------使用教程-----------------------------*/

//向下翻找到"自定义战斗"，输入以下指令编程战斗过程

//skill(a, b, c) 释放技能 (第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个)
//xskill(a, b, c) 换人释放技能 (第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个)
//Sskill(a, b, c) 不需要考虑换人，a可以选择1-8
//Sskill(a, b, c, d) 释放技能选择目标，d=0选择对面三人中的boss, 1-8选择己方位置（位置而不是角色）
//helper 使用支援者（只使用第一个支援者）
//roundOver 结束回合(持续到新的回合或者战斗结束)
//fullbp 全员蓄力
//exchange 全员交替
//run 撤退

//例：

//exchange  //前后排全部换人
//xskill 1, 1, 1  //1号位再换后排，1技能消耗1个豆子
//skill 2, 2, 0  //2号位2技能不蓄力
//skill 3, 1, 0  //3号位1技能不蓄力
//skill 4, 1, 3  //4号位1技能消耗3豆子
//helper  //召唤支援者
//roundOver  //回合结束
//新增选择施法对象功能，命令形式 Sskill_target(a, b, c, d) 
//参数 d 写 0 的话默认选择地方后排boss (三个敌人时） 1-8可以给己方位置施法（注意是位置而不是角色）
//已添加前三场斗技大赛的敌人坐标，具体用法参考 fight瓦尔坎
//Sskill_target 1, 1, 2, "瓦尔坎"  //1号位置使用1技能，消耗2个豆子，施法对象瓦尔坎

//AutoSkill用法：
 
//（根据敌人弱点自动释放技能，目前主要是篝火和历战能用，比写一套固定技能打怪快不少）
//1. 在"Function AutoSkill"里，case n 表示你第n个队伍的战斗方式 （等你了解怎么调用到这个case之后，可以随意写序号）
//2. 	自动技能举例：
//		If UTF8.InStr(1, WeakPoint, "暗") > 0 Then 	Sskill 5, 3, 0     ：如果敌方 有 暗弱点，就释放5号的3技能
//		ElseIf UTF8.InStr(1, WeakPoint, "扇") > 0 Then Sskill 5, 1, 0     ：如果敌方有 扇 弱点，就释放5号的1技能
//		Else Sskill 1, 1, 0    ：如果没有上述弱点，就释放1号的1技能
//3. 写好autoskill之后，在“选择counter队伍”模块，设置怪物-队伍的对应关系
// 例如： Camp2_Team(6) = Array(0, 3, 1, 2, 9) 表示 
//篝火2的第6张图（沙漠2）：第一个怪 用3号队伍，第二个怪 用1号队伍，第三个怪 用2号队伍，第四个怪 用9号队伍 （零不要改，占位用）

//自动放必杀功能：
//技能命令后面加上 _Ulti，如skill_Ulti，攒满bp后能自动释放必杀

/*------------------------------------------------------------------------------------------*/
/*--------------------------------------基础设置--------------------------------------------*/
/*------------------------------------------------------------------------------------------*/

//游戏包名（下面有已知服务器的包名，删掉//就可以用。不选的话，打开游戏后再启动脚本也可以读到包名）
//Dim app = Sys.GetFront()
//TracePrint("读取到包名"&app)
//Dim app = "com.netease.ma167"//网易
Dim app = "com.netease.ma167.bilibili" //b服

FW.NewFWindow("浮窗", 0, 1050, 1920, 30)
//创建文字控件
FW.Show ("浮窗")
FW.AddTextView "浮窗", "主窗口", "", 0, 0, 1400, 30
FW.AddTextView "浮窗", "即时信息", "脚本运行中", 1400, 0, 520, 30
FW.Opacity "浮窗", 0
FW.SetTextColor("主窗口","FFFFFF")
FW.SetTextColor("即时信息","FFFFFF")
FW.SetTextView ("即时信息", "", 1400, 0, 520, 30)

//识图模糊度（非常不建议降低！）
Dim ambiguity =0.98

//一些参数（记录遇到敌人的次数、记录前后排切换、用于洁哥一打一跑、用于判断需要休息）
Dim fatCatNum=0, doubleCatNum=0, normalEnemyNum=0, EX1=False, EX2=False, EX3=False, EX4=False, needRun = False, needRecover=False, coin=0
Dim intX,intY//用于返回地图坐标
dim 次数 = 1//用于历战
dim t = -1, initialTeam = -1, currentTeam = -1, targetTeam = -1//用于切换队伍
//地图序号初始化
Dim k = 0, j = 0
dim 日常mark = 0, 刷野用时 = 0, 日常用时 = 0, 花田用时 = 0, 羊毛用时 = 0, 篝火用时 = 0, 篝火1用时 = 0, 篝火2用时 = 0, 历战用时 = 0, 果炎用时 = 0
dim enum = 1//敌人序号初始化
Dim mark = 0
Dim TargetMap = 1
Dim coinNumk,coinNum

//声明地图位置坐标

dim Entry = Array()

//依次是：从篝火营地的入口，篝火1 每个地图的左入口，篝火2 每个地图的左入口
Entry(1) = {{800,705}, {445,1375},{535,1170}}
Entry(2) = {{800,1080},{445,1375},{435,1270}}
//Entry(3) = {{625,1270},{375,1345},{370,1200}}
//Entry(4) = {{435,1270},{445,1380},{435,1110}}
//Entry(5) = {{250,1080},{430,1280},{375,1200}}
//Entry(6) = {{250,705},{430,1280},{0,0}}
//Entry(7) = {{435,520},{430,1110},{450,1370}}
//Entry(8) = {{626,520},{370,1210},{435,1280}}
//由于篝火2地图没全开，脚本从地图6开始顺时针跑图的，以下地图其实是12345
//Entry(9) = {{800,705},  {445,1375},{535,1170}}
//Entry(10) = {{800,1080},{445,1375},{435,1270}}
//Entry(11) = {{625,1270},{375,1345},{370,1200}}
//Entry(12) = {{435,1270},{445,1380},{435,1110}}
//Entry(13) = {{250,1080},{430,1280},{375,1200}}

dim Camp1_Name()
Camp1_Name = Array("", "林", "雪", "原", "海", "山", "沙", "川", "崖")

dim Camp1 = Array()
//Camp1(1) = {{0,0},{800,897},{491,1031},{660,615}}
Camp1(2) = {{0,0},/*{860,897},*/{572,636}}
//Camp1(3) = {{0,0},{805,897}}
//Camp1(4) = {{0,0},{850,897}}
//Camp1(5) = {{0,0},{850,897}}
//Camp1(6) = {{0,0},{850,897}}
//Camp1(7) = {{0,0},{860,897}}
//Camp1(8) = {{0,0},{800,897}}
//以上坐标,从第一个元素起，依次是BOSS和百讨小怪

dim Camp1_Team = Array()
dim Camp1_Weak = Array()

//怪物的弱点
//Camp1_Weak(1) = Array("占位","剑斧扇火冰","剑枪弓雷暗","匕扇风")
Camp1_Weak(2) = Array("占位","匕弓扇火暗","剑斧冰光")
//Camp1_Weak(3) = Array("占位","匕弓杖冰风")
//Camp1_Weak(4) = Array("占位","剑枪斧雷光")
//Camp1_Weak(5) = Array("占位","剑弓杖火光")
//Camp1_Weak(6) = Array("占位","枪斧扇风光")
//Camp1_Weak(7) = Array("占位","剑匕书冰雷")
//Camp1_Weak(8) = Array("占位","枪弓书雷暗")

//篝火1队伍
//Camp1_Team(1)= Array(0, 1)
Camp1_Team(2)= Array(0, 1)
//Camp1_Team(3)= Array(0, 1)
//Camp1_Team(4)= Array(0, 1)
//Camp1_Team(5)= Array(0, 1)
//Camp1_Team(6)= Array(0, 1)
//Camp1_Team(7)= Array(0, 1)
//Camp1_Team(8)= Array(0, 1)

dim Camp2_Name()
Camp2_Name = Array("", "林2", "雪2", "原2", "海2", "山2", "沙2", "川2", "崖2", "林2", "雪2")

dim Camp2 = Array()
Camp2(6) = Array({0,0},{763,900},{451,1335},{282,1335},{622,618},{622,766})
Camp2(7) = Array({0,0},{813,900})
Camp2(8) = Array({0,0},{795,900})
Camp2(9) = Array({0,0},{810,897})
Camp2(10) = Array({0,0},{823,900},{525,640},{681,778},{681,1021})
Camp2(11) = Array({0,0},{813,900},{648,747},{648,1054})
Camp2(12) = Array({0,0},{820, 897},{690,775},{690,1022},{530,775},{530,1022})
Camp2(13) = Array({0,0},{811,898},{450,569},{252,569},{647,1052},{647,1228})
//以上坐标,从第一个元素起，依次是BOSS和磨石小怪

//篝火2怪物的弱点
dim Camp2_Weak = Array()
Camp2_Weak(6) = Array("占位","枪斧弓书火暗", "枪杖扇冰雷暗","剑斧书雷光","剑斧弓书火风","枪弓杖风暗")
Camp2_Weak(7) = Array("占位","匕弓冰风光")
Camp2_Weak(8) = Array("占位","剑弓冰雷光")
Camp2_Weak(9) = Array("占位","剑匕斧火风")
Camp2_Weak(10) = Array("占位","枪弓书火光","枪杖书火风","剑斧杖火暗","杖火雷光")
Camp2_Weak(11) = Array("占位","枪匕杖扇雷", "匕书冰雷暗", "枪匕杖冰光")
Camp2_Weak(12) = Array("占位","剑枪匕火风","剑弓杖火冰","弓扇雷风","剑斧书雷风","枪斧书冰光")
Camp2_Weak(13) = Array("占位","杖书扇风光","匕弓雷光","杖雷暗","书火风暗","弓扇火暗")
//历战一轮的顺序（弱点）
dim LizhanWeak = Array("占位","杖暗","扇光","匕风","弓火","枪冰","斧冰","书风","剑雷")
// 1.斧(杖暗）2.弓（扇光）3.书（匕风）4.枪（弓火）5.剑（枪冰）6.扇（斧冰）7.杖（书风）8.匕（剑雷）
/*----------------------------------------------------追忆之书用参数-----------------------------------------------*/
dim 主线=1,支线=2
dim 财富=1,权力=2,名声=3,斗技大赛=1
dim 财富高级=1,权力高级=1,名声高级=1,财富中级=2,权力中级=2,名声中级=2
dim 利杜=1,瓦尔坎=2,戈洛萨姆=3,缇奇莲=4//有新的斗技大赛时，这个数字要+1.或者直接在function 追忆之书写数字变量就行
/*----------------------------------------------------以上非必要不修改----------------------------------------------------*/
/*-----------------------------------------------------------------------------------------------------------------------*/	
/*----------------------------------------------------选择counter队伍----------------------------------------------------*/
//此处配置你的切换队伍依据
//注意Array里面第一个元素 0 是占位的，不要改。使用的队伍序号从第二个元素开始

//在此处声明每个历战你要使用的队伍序号。队伍序号1-10，数队伍界面最下面的小黄点	
dim LizhanTeam = Array(0,1,2,3,4,5,5,3,6)
// 1.斧 2.弓 3.书 4.枪 5.剑 6.扇 7.杖 8.匕

//在此处声明篝火2怪物使用的队伍序号，地图6是沙漠2，顺时针
dim Camp2_Team = Array()
Camp2_Team(6) = Array(0, 6, 1, 1, 1, 1)
Camp2_Team(7) = Array(0, 1)
Camp2_Team(8) = Array(0, 4)
Camp2_Team(9) = Array(0, 3)
Camp2_Team(10) = Array(0, 6, 1, 1, 1)
Camp2_Team(11) = Array(0, 7, 1, 1)
Camp2_Team(12) = Array(0, 3, 1, 1, 1, 1)
Camp2_Team(13) = Array(0, 5, 1, 1, 1, 1)
/*--------------------------------------------------------日常任务----------------------------------------------------*/
//通过删除字母前面的“//”来更改刷怪地点，比如想要用叹息冰窟刷怪，找到“//txbk”，改成“txbk”即可




/*百讨

Function 百讨()
    TracePrint"*********************************************尝试执行getExp**********************************************"
    Dim loopTime=0
    While true //循环直到回城恢复  
        loopTime = loopTime + 1
        TracePrint"循环次数"&loopTime
        If inWorld() Then //世界中则原地水平移动
            loopTime=0	
            moveY 
        End If
        
        If inFight() Then   //遇到战斗
            loopTime=0
            TracePrint "检测到战斗" 
            kill123 
        End If
    	
        If fightSettlement() Then //战斗结算时
            settlementOver 
        End If
       
        Delay 300
    Wend
End Function

Function kill123()
 resetEX 
   If inFight() Then 
      
     fullbp 
     roundOver 
     
     run
      
    End If
End Function*/



日常1 //顺序执行开关自动交替\花田、羊毛、果炎、一键收菜、篝火、历战NPC等
//一点小心意(1)
//果炎
//看广告
//刚魔石1(9)
//刚魔石2(9)
//开关自动交替
//红龙(8)
//追忆碎片
//冒险家(1)
//牛(9)
//花田
//羊毛
//一键收菜
//Campfire1 (1)//篝火1boss,括号里声明使用队伍序号
//Campfire2//篝火2boss+磨石   ----不打崖2boss，已删除； 川2boss和雪2变色龙 需要你在“ 以下为篝火2的战斗指令 ”后面修改
//Lizhan 0, 0, 1
//useTeam 10
//追忆之书 主线, 权力, 权力中级, 2000
//第一个变量：战斗对象。输入 0 就全部打一遍
//第二个变量：战斗类型。0：历装材料，1：收服支援（刷武器）
//第三个变量：循环次数。赢取历装材料一天只能 1 次。
//历战一轮的顺序（弱点）
// 1.斧(杖暗）2.弓（扇光）3.书（匕风）4.枪（弓火）5.剑（枪冰）6.扇（斧冰）7.杖（书风）8.匕（剑雷）
//Lizhan 2, 1, 1//抓8个历战NPC支援

/*----------------------------------------------------设置刷怪地点----------------------------------------------------*/
//txbk //叹息冰窟
//dslz //大树露珠
//wmpb //雾明瀑布

dim startTime = 4
dim endTime = 8//凌晨4点到8点，如果在刷野，就去做一轮日常。

//(增加了选择队伍功能,9表示用队伍9）
//zzzd(9) //针柱之洞 
//sfsg(9) //授富的砂宫
//jyls(9) //久远的流沙
//zjh(9)//中津海
//rtqk(9)//热腾的泉窟
//getExp //原地刷怪（重启游戏/回城恢复后脚本会终止）

//newgetExp

//自动战斗//用于跑图，野外遇怪自动战斗

//跑路//用于跑图，野外遇怪自动逃跑


/*----------------------------------------------------追忆之书----------------------------------------------------*/
//命令最后的数字为循环次数
//改变功能的话，需要写好战斗技能轴并在在Function 追忆之书里调用。例子：Function fight瓦尔坎 

//追忆之书 支线, 斗技大赛, 利杜, 96
//追忆之书 支线, 斗技大赛, 瓦尔坎, 96
useTeam 10
追忆之书 主线, 名声, 名声中级, 2000


/*------------------------------------------------------------------------------------------------------------------------------*/
/*--------------------------------------------------------功能设置--------------------------------------------------------------*/
/*------------------------------------------------------------------------------------------------------------------------------*/



/*----------------------------------------------设置遇到不同敌人时的战斗流程----------------------------------------------*/
//通过写入流程名的方式来修改战斗流程。具体的战斗流程在下一部分“自定义战斗流程”中。
Function chooseFight()
    readyToFight
    If fatCat() Then 
        fatCatNum = fatCatNum + 1
        //SnapShot "/sdcard/qllr/cat55/" & fatCatNum & ".png"
        /****************下面写遇到55级肥猫的战斗流程*****************/
        
        killFatCat //脚本提供的百分百杀肥猫的方法（注意需要专门编队和支援者，详情看下一部分“自定义战斗流程”）
        //EXkill //轮换蓄力A猫（默认）
		
    ElseIf doubleCat() Then
        doubleCatNum = doubleCatNum + 1
        //SnapShot "/sdcard/qllr/cat50/" & doubleCatNum & ".png"
        /*****************下面写遇到50级双猫的战斗流程*****************/
        
        killDoubleCat //脚本提供的百分百杀双猫的方法（注意需要专门编队和支援者，详情看下一部分“自定义战斗流程”）
        //EXkill //轮换蓄力A猫（默认）
    Else 
        normalEnemyNum = normalEnemyNum + 1
        //SnapShot "/sdcard/qllr/kalami/" & normalEnemyNum & ".png"
        /*****************下面写遇到普通敌人的战斗流程*****************/
        //run
        //战斗到底
        kill//默认方法（一号位一技能蓄力）
        //runAndKill //一打一跑
    End If
    
    dim lp = 0
    While IsNumeric(image.OcrText(780, 1710, 830, 1820, 0, 1)) = False and lp < 6
        lp = lp + 1
    Wend
    coinNumk = image.OcrText(780, 1580, 830, 1690, 0, 1)
    coinNum = image.OcrText(780, 1710, 830, 1820, 0, 1)
    If IsNumeric(coinNumk) and IsNumeric(coinNum) Then
        coin = coin + coinNumk * 1000 + coinNum
    End If
    刷野用时 = Round(TickCount() /60000,1) - 日常用时
    
    TracePrint "自动刷怪     运行" & Round(TickCount() /60000,1) & "分钟     55猫" & fatCatNum & "次     50猫" &_
     doubleCatNum & "次     小怪" & normalEnemyNum & "次     获得金币：" & coin & "     时薪：" & Round(coin/Round(TickCount() /60000,1)*60,0) 
	
    //ShowMessage "运行" & 刷野用时 & "分钟,总战斗" & fatCatNum + doubleCatNum + normalEnemyNum & "次，其中55猫" & fatCatNum & "次，双猫" & doubleCatNum & "次。获得金币:" & coin
	
    FW.SetTextView("主窗口", "自动刷怪     运行" & Round(TickCount() /60000,1) & "分钟     55猫" & fatCatNum & "次     50猫" &_
     doubleCatNum & "次     小怪" & normalEnemyNum & "次     获得金币：" & coin & "     时薪：" & Round(coin/Round(TickCount() /60000,1)*60,0), 0, 0, 1400, 30)
End Function

Function 提桶跑路()
	
    rem start1

    While infight() = false
        delay 200
    Wend

    While inFight()
        readyToFight
        run
        roundOver
    Wend
    backWorld
    goto start1  
End Function


Function 日常(startTime,endTime)

    Exit Function
    //不需要自动日常的话，把上面的Exit Function打开。
    //通宵挂野外时，如果时间过了4点，就自动去做一轮日常。
    //8点以后就不去了。
    //暂不支持连续两天。
    //
    If DateTime.format("%H") + 0 >= 4 and DateTime.format("%H") + 0 < 8 and 日常mark = 0 Then 
        restartGame//通宵在线的话，需要重启才能刷新小镇资源
        //------------------------下面按需增删日常内容---------------------
        花田
        一键收菜
        Campfire1 (1)
        Campfire2
        Lizhan 2, 1, 1
        //------------------------下面两个不要改--------------------------
        日常 = True
        日常mark = 1
    End If
	
    /*If DateTime.format("%H") + 0 >= 16 and DateTime.format("%H") + 0 < 18 and 日常mark = 0 Then 
		//------------------------下面按需增删日常内容---------------------
		Campfire2
		//------------------------下面两个不要改--------------------------
		日常 = True
		日常mark = 1
	End If*/
	
End Function

Function 日常1
    //开关自动交替
    果炎
    花田
    追忆碎片 
    看广告 
    一键收菜 
    一点小心意(1)
    //冒险家(1) 
    //牛 (9)
    //红龙(8)
    //Campfire1 (1)
    //Campfire2 
    //Lizhan 2, 1, 1
    //开关自动交替 
    //刚魔石1(9)
    //刚魔石2(9)
End Function


/*-------------------------------------------------
需要恢复的条件-------------------------------------------------*/
//通过更改If后面的等式/不等式来修改需要恢复的条件。
//hp(n)指的是n号位的血量，mp(n)指的是n号位的蓝量。 只支持检测1-4号位。
//hp(n)=0说明角色目前绿血或者有盾，=1说明黄血，=2说明红血，=3说明检测不到血条了
//mp(n)=0说明蓝条长于25%，=1说明蓝条短于25%或者检测不到蓝条


Function ifNeedRecover()
    //更改下面一行If到Then之间的条件即可。如果满足条件就说明需要恢复。默认判断1-4号位蓝条和1号位血条。
    // 两人缺蓝
    //delay 2000//等待buff飘过
    If  matchPointColor(1090 - 215 * 1, 1700, "000000", 1)_
    and matchPointColor(1090 - 215 * 2, 1700, "000000", 1)_
    and matchPointColor(1090 - 215 * 3, 1700, "000000", 1)_
    and matchPointColor(1090 - 215 * 4, 1700, "000000", 1) then
        traceprint "HP SP检测中……"
        FW.SetTextView ("即时信息", "HP SP检测中……", 1400, 0, 520, 30)
        If hp(1) > 1 or hp(2) > 1 or hp(3) > 1 or hp(4) > 1 Then 
            needRecover = True
            TracePrint "*****HP低，需要恢复！*****"
            FW.SetTextView ("即时信息", "HP低，需要恢复！", 1400, 0, 520, 30)
        ElseIf sp(1) = 1 or sp(2) = 1 or sp(3) = 1 or sp(4) = 1 Then
            needRecover = True
            TracePrint "*****SP低，需要恢复！*****"
            FW.SetTextView ("即时信息", "S低，需要恢复！", 1400, 0, 520, 30)
        Else 
            needRecover = False
            TracePrint "*****不需要恢复！*****"
            FW.SetTextView ("即时信息", "不需要恢复！", 1400, 0, 520, 30)
        End If
    Else 
        traceprint "结算中或者状态被遮挡，无法判断！"
        FW.SetTextView ("即时信息", "结算中或者状态被遮挡，无法判断！", 1400, 0, 520, 30)
    End If
    
End Function



/*--------------------------------------------------------------------------------------------------------------------------*/
/*---------------------------------------------------自定义战斗流程----------------------------------------------------------*/
/*--------------------------------------------------------------------------------------------------------------------------*/
//简单提供了一些常用的战斗流程。可以编写自己的战斗流程。

Function 战斗到底()
    TracePrint "******************尝试执行killFatCat*******************"
    FW.SetTextView ("即时信息", "尝试执行killFatCat", 1400, 0, 520, 30)
    If inFight() Then 
      
    End If
End Function



/*-----------------------------------------百分百杀55肥猫--------------------------------------------*/

Function killFatCat()
    TracePrint "******************尝试执行killFatCat*******************"
    FW.SetTextView ("即时信息", "尝试执行killFatCat", 1400, 0, 520, 30)
    If inFight() Then 
        While inFight()
          
        Wend
    End If
        
End Function

Function killDoubleCat()
    TracePrint "******************尝试执行killDoubleCat*******************"
    FW.SetTextView ("即时信息", "尝试执行killDoubleCat", 1400, 0, 520, 30)
    If inFight() Then 
        While inFight()
         
        Wend
    End If
End Function

/*-----------------------------------------轮换蓄力战斗--------------------------------------------*/
Function EXkill()
    TracePrint "***********************尝试执行EXkill************************"
    FW.SetTextView ("即时信息", "尝试执行EXkill", 1400, 0, 520, 30)
    While inFight()
     
    Wend
   
End Function


/*---------------------------------------EX洁秒杀杂鱼------------------------------------------*/
Function kill()
    TracePrint"******************尝试执行kill*******************"
    FW.SetTextView ("即时信息", "正在秒杀杂鱼", 1400, 0, 520, 30)
    If inFight() Then 
        Click 114, 737
        roundOver_24x7 
    End If 
End Function


/*---------------------------------------EX洁一打一跑------------------------------------------*/
//配队需求：
//3号位 EX洁卡利特 1技能 化枪为剑
Function runAndKill()
    TracePrint"***********************尝试执行runAndKill************************"

    If Not needRun Then 
        While inFight()
            needRun=True
            Sskill 1, 1, 0  //把ex洁放在4号位，化剑放在1技能位置，炎枪放在2技能位置（平A算是0技能）
            fullbp
            roundOver 
        Wend
    ElseIf needRun Then 
        needRun=False
        run 
    End If    
End Function


Function fight追忆(option3)
    resetEX
    While inFight() <> True
        delay 20
    Wend
    TracePrint "进入战斗"
    FW.SetTextView ("即时信息", "进入战斗", 1400, 0, 520, 30)
    readyToFight 


    Select Case option3


    Case 名声中级

/*----------------------------------------场次 1--------------------------------------------*/
        //回合 1
        Click 114, 737
        roundOver_24x7
/*------------------------------------------------------------------------------------------*/		
        traceprint "第一场结束"
        FW.SetTextView ("即时信息", "第一场结束", 1400, 0, 520, 30)

        cutScene//过场动画

        resetEX 
        While inFight() <> True
            delay 20
        Wend
        TracePrint "进入战斗"
        FW.SetTextView ("即时信息", "进入战斗", 1400, 0, 520, 30)
        readyToFight 
/*---------------------------------------场次 2---------------------------------------------*/	
        //回合 1
        Click 114, 737
        roundOver_24x7
/*------------------------------------------------------------------------------------------*/
        traceprint "第二场结束"
        FW.SetTextView ("即时信息", "第二场结束", 1400, 0, 520, 30)



	
    Case 利杜
        resetEX 
        click 363, 515
        click 363, 515
        //回合 1
        Sskill 5, 2, 3 
        Sskill 2, 3, 0
        Sskill 3, 3, 0
        Sskill 4, 3, 3
        roundOver_24x7
        If hp_Die() =True Then 
            run_zhuiyi 
            Exit Function
        End If
        
        //回合 2
        Sskill 1, 3, 0
        Sskill 6, 2, 3
        Sskill 4, 1, 0
        roundOver_24x7
        If hp_Die() =True Then 
            run_zhuiyi 
            Exit Function
        End If
        
        //回合 3
        Sskill 2, 4, 2
        Sskill 7, 1, 3
        roundOver_24x7
        If hp_Die() =True Then 
            run_zhuiyi 
            Exit Function
        End If
        
        //回合 4
        Sskill 1, 3, 2
        Sskill 2, 3, 0
        Sskill 3, 3, 2
        Sskill 4, 1, 3
        helper
        roundOver_24x7
        If hp_Die() =True Then 
            run_zhuiyi 
            Exit Function
        End If
        
        //回合 5
        Sskill 1, 3, 3
        Sskill 2, 2, 1
        Sskill 3, 3, 3
        Sskill 4, 5, 0
        roundOver_24x7
        If hp_Die() =True Then 
            run_zhuiyi 
            Exit Function
        End If
        
        //回合 6
        Sskill 5, 5, 0
        Sskill 2, 2, 3
        Sskill 3, 5, 0
        Sskill 4, 1, 2
        roundOver_24x7
        If hp_Die() =True Then 
            run_zhuiyi 
            Exit Function
        End If
        
        If infight() Then//没打死快跑吧
            run_zhuiyi
        End If
    End Select
	
    cutScene//过场动画
	
    waitAndClick(230, 939, 265, 1020,"确定",240,980)//战斗结束后 点击 确定
    click 470,960//点击关闭


End Function


Function AutoSkill(team, WeakPoint)
    resetEX 
	
    dim buff = 0
    dim debuff = 0
    dim 洁哥无损 = 0
    //前面这些是用于：一排两个人都打不到弱点时，放一个通用技能，然后下回合根据这个标记来换技能。
    //编写顺序推荐：后排、多段攻击、冷门弱点、耗蓝低的技能写前面，前后排技能使用几率差不多就交叉写。
	
    Select Case team
	
    Case 1 //------------------------------------队伍1的自动技能逻辑-------------------------------------------------
        //
        //-------------------------------------------------------------------------------回合  1
        //位置1
        If UTF8.InStr(1, WeakPoint, "剑") > 0 Then
            Sskill 1, 3, 0//菲欧儿
        ElseIf UTF8.InStr(1, WeakPoint, "斧") > 0 Then
            Sskill 5, 1, 0//特欧
        Else 
            Sskill 1, 3, 0//菲欧儿
        End If
        //位置2
        If  UTF8.InStr(1, WeakPoint, "暗") > 0 Then
            Sskill 2, 2, 0//普利姆罗洁
        ElseIf UTF8.InStr(1, WeakPoint, "扇") > 0 Then
            Sskill 2, 1, 0//普利姆罗洁
        ElseIf UTF8.InStr(1, WeakPoint, "匕") > 0 Then
            Sskill 6, 1, 0//薇欧拉
        Else
            Sskill 6, 3, 0//薇欧拉debuff
            debuff = 1
        End If
        //位置3
        If UTF8.InStr(1, WeakPoint, "剑") > 0 Then
            Sskill 3, 1, 0//洁卡利特化枪为剑
        ElseIf UTF8.InStr(1, WeakPoint, "枪") > 0 Then
            Sskill 3, 3, 0//洁卡利特化枪为剑
        ElseIf UTF8.InStr(1, WeakPoint, "弓") > 0 Then
            Sskill 7, 2, 0//稻草人
        ElseIf UTF8.InStr(1, WeakPoint, "风") > 0 Then
            Sskill 7, 3, 0//稻草人
        Else
            Sskill 3, 1, 0//洁卡利特化枪为剑
        End If
        //位置4
        If UTF8.InStr(1, WeakPoint, "火") > 0 Then
            Sskill 4, 1, 0//塞拉斯火3
        ElseIf UTF8.InStr(1, WeakPoint, "冰") > 0 Then
            Sskill 4, 2, 0//塞拉斯冰3
        ElseIf UTF8.InStr(1, WeakPoint, "雷") > 0 Then
            Sskill 4, 3, 0//塞拉斯雷3
        ElseIf UTF8.InStr(1, WeakPoint, "匕") > 0 Then
            Sskill 8, 2, 0//亚黛拉
        ElseIf UTF8.InStr(1, WeakPoint, "光") > 0 Then
            Sskill 8, 3, 0//亚黛拉
        Else 
            Sskill 8, 1, 0//亚黛拉无视弱点匕3
        End If
        //
        fullbp
        roundOver
        //
        //-------------------------------------------------------------------------------回合  2
        If inFight() Then 
            //位置1
            If UTF8.InStr(1, WeakPoint, "斧") > 0 Then
                Sskill 5, 1, 0//特欧
            ElseIf UTF8.InStr(1, WeakPoint, "剑") > 0 Then
                Sskill 1, 3, 0//菲欧儿剑
            Else 
                Sskill 5, 1, 0//特欧
            End If
            //位置2
            If UTF8.InStr(1, WeakPoint, "匕") > 0 Then
                Sskill 6, 1, 0//薇欧拉
            ElseIf UTF8.InStr(1, WeakPoint, "暗") > 0 Then
                Sskill 2, 2, 0//普利姆罗洁
            ElseIf UTF8.InStr(1, WeakPoint, "扇") > 0 Then
                Sskill 2, 1, 0//普利姆罗洁
            Else
                Sskill 2, 3, 0//普利姆罗洁buff
                buff = 1
            End If
            //位置3
            If UTF8.InStr(1, WeakPoint, "弓") > 0 Then
                Sskill 7, 2, 0//稻草人
            ElseIf UTF8.InStr(1, WeakPoint, "风") > 0 Then
                Sskill 7, 3, 0//稻草人
            ElseIf UTF8.InStr(1, WeakPoint, "剑") > 0 Then
                Sskill 3, 1, 0//洁卡利特
            ElseIf UTF8.InStr(1, WeakPoint, "枪") > 0 Then
                Sskill 3, 3, 0//洁卡利特
            Else
                Sskill 7, 2, 0//稻草人
            End If
            //位置4
            If UTF8.InStr(1, WeakPoint, "匕") > 0 Then
                Sskill 8, 2, 0//亚黛拉
            ElseIf UTF8.InStr(1, WeakPoint, "光") > 0 Then
                Sskill 8, 3, 0//亚黛拉	
            ElseIf UTF8.InStr(1, WeakPoint, "火") > 0 Then
                Sskill 4, 1, 0//塞拉斯火3
            ElseIf UTF8.InStr(1, WeakPoint, "冰") > 0 Then
                Sskill 4, 2, 0//塞拉斯冰3
            ElseIf UTF8.InStr(1, WeakPoint, "雷") > 0 Then
                Sskill 4, 3, 0//塞拉斯雷3
            Else 
                Sskill 4, 1, 0//塞拉斯火3
            End If
            //
            fullbp
            roundOver 
            //
        End If
        //
        //-------------------------------------------------------------------------------回合  3
        If inFight() Then 
            //位置1
            If UTF8.InStr(1, WeakPoint, "剑") > 0 Then
                Sskill 1, 3, 0//菲欧儿
            ElseIf UTF8.InStr(1, WeakPoint, "斧") > 0 Then
                Sskill 5, 1, 0//特欧
            Else 
                Sskill 1, 3, 0//菲欧儿
            End If
            //位置2
            If  UTF8.InStr(1, WeakPoint, "暗") > 0 Then
                Sskill 2, 2, 0//普利姆罗洁
            ElseIf UTF8.InStr(1, WeakPoint, "扇") > 0 Then
                Sskill 2, 1, 0//普利姆罗洁
            ElseIf UTF8.InStr(1, WeakPoint, "匕") > 0 Then
                Sskill 6, 1, 0//薇欧拉
            Else
                Sskill 6, 4, 0//薇欧拉无视弱点削盾
            End If
            //位置3
            If UTF8.InStr(1, WeakPoint, "剑") > 0 Then
                Sskill 3, 1, 0//洁卡利特化枪为剑
            ElseIf UTF8.InStr(1, WeakPoint, "枪") > 0 Then
                Sskill 3, 3, 0//洁卡利特化枪为剑
            ElseIf UTF8.InStr(1, WeakPoint, "弓") > 0 Then
                Sskill 7, 2, 0//稻草人
            ElseIf UTF8.InStr(1, WeakPoint, "风") > 0 Then
                Sskill 7, 3, 0//稻草人
            Else
                Sskill 3, 1, 0//洁卡利特化枪为剑
            End If
            //位置4
            If UTF8.InStr(1, WeakPoint, "火") > 0 Then
                Sskill 4, 1, 0//塞拉斯火3
            ElseIf UTF8.InStr(1, WeakPoint, "冰") > 0 Then
                Sskill 4, 2, 0//塞拉斯冰3
            ElseIf UTF8.InStr(1, WeakPoint, "雷") > 0 Then
                Sskill 4, 3, 0//塞拉斯雷3
            ElseIf UTF8.InStr(1, WeakPoint, "匕") > 0 Then
                Sskill 8, 2, 0//亚黛拉
            ElseIf UTF8.InStr(1, WeakPoint, "光") > 0 Then
                Sskill 8, 3, 0//亚黛拉
            Else 
                Sskill 8, 1, 0//亚黛拉无视弱点匕3
            End If
            //
            fullbp
            roundOver 
            //
        End If

        While inFight()
            exchange
            fullbp
            roundOver
        Wend 
    
    
        //在这里写其他队伍的自动技能逻辑
    
    
    End Select

    If fightSettlement() Then //战斗结算时
        settlementOver 
    End If
    Delay 300

End Function


/*---------------------------------------暂停战斗------------------------------------------*/
Function stopFight()
    TracePrint"******************尝试执行stopFight*******************"
    FW.SetTextView ("即时信息", "尝试执行stopFight", 1400, 0, 520, 30)
    While inFight()
        Delay 1000
    Wend
End Function

/*------------------------------------------------------------------------------------------*/
/*--------------------------------------新增功能--------------------------------------------*/
/*------------------------------------------------------------------------------------------*/


Function useTeam(targetTeam)

    delay 1000//增加延迟，等待浮窗消失 避免浮窗遮挡队伍黄点
    If targetTeam <> currentTeam Then 
        backWorld
        TracePrint "目标队伍序号： " & targetTeam
        FW.SetTextView ("即时信息", "目标队伍序号： " & targetTeam, 1400, 0, 520, 30)

        //click 180,330
        While matchPointColor(1048, 41, "E9E9E9", 1) <> true
            click 180, 330	
        Wend

        //读取初始队伍序号（1-10），用于后续返回
        If initialTeam = -1 Then
            For t = 1 To 10
                If matchPointColor(53, 935 + t * 42, "00DEFF", 7) = true Then 
                    initialTeam = t
                End If
            Next
        End If
        TracePrint "初始队伍序号： " & initialTeam & "     (序号-1说明尚未切换队伍）"
        FW.SetTextView ("即时信息", "初始队伍序号： " & initialTeam, 1400, 0, 520, 30)
        //读取当前队伍序号（1-10）
        For t = 1 To 10
            If matchPointColor(53, 935 + t * 42, "00DEFF", 7) = true Then 
                currentTeam = t
                TracePrint "当前队伍序号： " & currentTeam
                FW.SetTextView ("即时信息", "当前队伍序号： " & currentTeam, 1400, 0, 520, 30)
            End If
        Next

        //切换到目标队伍
        If targetTeam > currentTeam Then 
            If targetTeam - currentTeam <= 5 Then 
                For c = 1 To targetTeam - currentTeam
                    click 500, 1830
                Next
            Else 
                For c = 1 To currentTeam + 10 - targetTeam
                    click 500, 510
                Next 
            End If

        ElseIf targetTeam < currentTeam Then
            If currentTeam - targetTeam <= 5 Then 
                For c = 1 To currentTeam - targetTeam
                    click 500, 510
                Next
            Else 
                For c = 1 To targetTeam + 10 - currentTeam
                    click 500, 1830
                Next
            End If
        End If

        //读取当前队伍序号（1-10），确认已切换完成
        For t = 1 To 10
            If matchPointColor(53, 935 + t * 42, "00DEFF", 7) = true Then 
                currentTeam = t
                TracePrint "当前队伍序号： " & currentTeam
                FW.SetTextView ("即时信息", "当前队伍序号： " & currentTeam, 1400, 0, 520, 30)
            End If
        Next

        If currentTeam <> targetTeam Then 
            useTeam (targetTeam)
        End If


        TracePrint "已切换到目标队伍： " & currentTeam
        FW.SetTextView ("即时信息", "已切换到目标队伍： " & currentTeam, 1400, 0, 520, 30)
        click 1050,1855
        backWorld 

    End If

End Function


/*Function useTeam(i)//新界面栏
	
    delay 1000//增加延迟，等待浮窗消失 避免浮窗遮挡队伍黄点
    
        backWorld
        TracePrint "目标队伍序号： " & i
        FW.SetTextView ("即时信息", "目标队伍序号： " & i, 1400, 0, 520, 30)

        //click 180,330
        While matchPointColor(1048, 41, "E9E9E9", 1) <> true
            click 180, 330	
        Wend
        
        //读取初始队伍序号（1-10），用于后续返回
        If initialTeam = t Then
            For t = 1 To 10
                If matchPointColor(834, 1870 + t * 72, "90DCED", 7) = true Then 
                    initialTeam = t
                End If
            Next
        End If
        TracePrint "初始队伍序号： " & initialTeam & "     (序号-1说明尚未切换队伍）"
        FW.SetTextView ("即时信息", "初始队伍序号： " & initialTeam, 1400, 0, 520, 30)
        //读取当前队伍序号（1-10）
        For t = 1 To 10
            If matchPointColor(834, 1870 + t * 72, "90DCED", 7) = true Then 
                currentTeam = t
                TracePrint "当前队伍序号： " & currentTeam
                FW.SetTextView ("即时信息", "当前队伍序号： " & currentTeam, 1400, 0, 520, 30)
            End If
        Next
	
    Select Case i //选择队伍编号

    Case 1 
        slowclick 834, 187

    Case 2 
        slowclick 762,1870

    Case 3 
        slowclick 690,1870
		
    Case 4 
        slowclick 618,1870

    Case 5 
        slowclick 546,1870

    Case 6 
        slowclick 474,1870

    Case 7 
        slowclick 402,1870

    Case 8 
        slowclick 330, 1870
        
    Case 9 
        slowclick 258, 1870
        
    Case 10 
        slowclick 186, 1870
        
    End Select
    
    //读取当前队伍序号（1-10），确认已切换完成
    For t = 1 To 10
    If matchPointColor(834, 1870 + t * 72, "90DCED", 7) = true Then 
       currentTeam = t
      TracePrint "当前队伍序号： " & currentTeam
      FW.SetTextView ("即时信息", "当前队伍序号： " & currentTeam, 1400, 0, 520, 30)
    End If
    Next
    
        click 1050,1855
        backWorld 
End Function*/

Function tpSleep(i)

    // 1.瓦洛雷		2.恩波格洛	3.希亚特珀利斯	4.利布尔泰德	5.牧羊岩		6.桑谢德		7.库利亚布鲁克	8.克拉古斯比亚
    // 1.斧*****		2.弓****		3.书**			4.枪*		5.剑*		6.扇**		7.杖**			8.匕*
    backWorld 
    openMap 
    tpTown (i)

    Swipe 300,300, 500,300//上滑进入旅馆
    While inGame() And Not matchPic("Bead")
        Delay 200
        TracePrint "-----------找床中-----------"
        FW.SetTextView ("即时信息", "找床中", 1400, 0, 520, 30)
    Wend
    click intX + 15, intY + 18 //点击床图标
    
    Delay 400
    click 322, 1198
    Delay 400
    click 322, 1198//加两下点击防卡住
    
    While inGame() And Not inWorld() //不在地图中说明睡觉没成功，则等待
        Delay 200
        click 322, 1198 //关闭睡觉成功对话框
    Wend
    TracePrint "睡觉成功"
    FW.SetTextView ("即时信息", "睡觉成功", 1400, 0, 520, 30)
    //回到城镇i
    click 874, 1618//打开小地图
    delay 300//避免小地图还没打开就执行下一步

    If i = 5 Then
        Click 407, 827
    ElseIf i = 6 then
        Click 478,1043
    Else
        While inGame() And Not matchPic("Door")
            Delay 200
            TracePrint "-----------找门中-----------"
            FW.SetTextView ("即时信息", "找门中", 1400, 0, 520, 30)
        Wend
        Click intX + 25, intY + 20 //走到门外
    End If
    
    While inWorld() <> True 
        Delay 200
    Wend
    TracePrint "回到城镇" & i
    FW.SetTextView ("即时信息", "回到城镇" & i, 1400, 0, 520, 30)
End Function

Function MatchPic(Pic)
    FindPic 0,0,0,0,"Attachment:" & Pic & ".png","000000",1,0.75,intX,intY
    If intX > -1 And intY > -1 Then
        TracePrint intX & "," & intY
        MatchPic = True
    Else 
        MatchPic = False
    End If
End Function






Function Lizhan(序号, 类型, 次数)

    历战用时 =  Round(TickCount() /60000,1)
    If 类型 = 0 Then 
        次数 = 1
    End If
    If 序号 = 0 and 类型 = 1 Then 
        dismissHelper//序号0类型1表明抓一圈历战支援。如果第＞1个历战在支援列表，会把前面的都给告别了。所以直接在这里全告别。
    End If

    If 序号 > 0 Then 

        tpSleep (序号)
        gotoLizhan (序号)
	
        for t = 1 to 次数
            useTeam LizhanTeam(序号)
			
            SelectLizhanFight 序号, 类型
            fightLizhan (序号)
            FW.SetTextView ("主窗口", "历战 "& 序号 & " 完成" & 次数 & "次", 0, 0, 1400, 30)
            if 次数 > 1 then//单刷时在这里告别，节省对话的判断时间。打一次的话打完留着支援
                dismissHelper 
            End If	
			
            If needRecover And inWorld() Then  //需要恢复时------注意：判断可能失误，有蓝但是不够再打一次！建议去掉这个if，打完直接恢复
                TracePrint "尝试休息"
                FW.SetTextView ("即时信息", "尝试休息", 1400, 0, 520, 30)
                If  matchPointColor(330,1782, "2F2F31",1) Then //有通行证恢复次数
                    TracePrint "有恢复次数"
                    FW.SetTextView ("即时信息", "有恢复次数", 1400, 0, 520, 30)
                    recover 
                Else 
                    tpSleep (序号)
                    gotoLizhan (序号)
                End If
            End If
        Next
    Else 
        For i = 1 To 8
            tpSleep (i)
            gotoLizhan (i)
            useTeam LizhanTeam(i)
            SelectLizhanFight i, 类型
            fightLizhan(i)
        Next
    End If

    //切换回初始队伍 
    If initialTeam <> -1 Then 
        useTeam initialTeam
    End If

    历战用时 = Round(TickCount() / 60000, 1) - 历战用时

    FW.SetTextView ("主窗口", "历战完成", 0, 0, 1400, 30)
End Function





Function gotoLizhan(i)
	
    click 874, 1618//打开小地图
    delay 300//避免小地图还没打开就执行下一步
	
    Select Case i //选择传送编号

    Case 1 //瓦洛雷
        click 360, 443//去瓦洛雷大街
        While inWorld() <> True
            Delay 200
        Wend
        moveMinimap 380,1280

    Case 2 //恩波格洛
        click 400, 1398//去恩波格洛东街
        While inWorld() <> True
            Delay 200
        Wend
        moveMinimap 263,1013

    Case 3 //希亚特珀利斯
        click 450,675//去希亚特珀利斯图书馆
        While inWorld() <> True
            Delay 200
        Wend
        moveMinimap 610,970

    Case 4 //利布尔泰德
        click 580,1200//去老太太家里
        While inWorld() <> True
            Delay 200
        Wend
        moveMinimap 590,1050

    Case 5 //牧羊岩
        moveMinimap 500,1180

    Case 6 //桑谢德
        moveMinimap 670,430

    Case 7 //库利亚布鲁克
        moveMinimap 625, 1130

    Case 8 //克拉古斯比亚
        click 150,1260//去恩波格洛东街
        While inWorld() <> True
            Delay 200
        Wend
        moveMinimap 280,1085

    End Select

	
End Function

Function SelectLizhanFight(i, type)
    Select case i

    Case 1 //瓦洛雷
        click 540, 1200//点击小人

    Case 2 //恩波格洛
        click 526,1012//点击小人

    Case 3 //希亚特珀利斯
        click 550,1030//点击小人
			
    Case 4 //利布尔泰德
        click 540,1210//点击小人

    Case 5 //牧羊岩
        click 570,860//点击小人

    Case 6 //桑谢德
        click 515,830//点击小人

    Case 7 //库利亚布鲁克
        click 440,1040//点击小人

    Case 8 //克拉古斯比亚
        click 560, 1000
    End Select
    

    While (Not matchPointColor(160, 1720, "2D4177", 1) And Not matchPointColor(160, 1840, "2D4177", 1))//等待右下角打探图标出现
        Delay 200
        TracePrint "-----------等待右下角打探出现-----------"
        FW.SetTextView ("即时信息", "等待右下角打探出现", 1400, 0, 520, 30)
    Wend
    
    If type = 1 and ((matchPointColor(170, 1490, "818181", 5) And matchPointColor(150, 1490, "A8A860", 5))_
		or (matchPointColor(170,1468, "818181", 5) And matchPointColor(150,1468, "A8A860", 5))) Then 

        dismissHelper
		
        SelectLizhanFight i, type
        Exit Function	
    End If
    
    Click 135,1785 //点击打探
    		
    While inGame() And (Not matchPointColor(279,182,"FFFFFF",5) and Not matchPointColor(279,173,"FFFFFF",5))
        Delay 200
        TracePrint "-----------等待选择界面-----------"
        FW.SetTextView ("即时信息", "等待选择界面", 1400, 0, 520, 30)
    Wend
    
    

    If type = 0 and matchPointColor(645,1400,"5567BF",5)Then //选择赢取历装材料，且当日未获取(赢取颜色亮红）
        click 660, 1560//赢取
        while not matchPointColor(467,429,"FFFFFF",5)//历装材料图标
            Delay 200
        Wend
        click 230, 1150
        Delay 300
        click 300,1200
        traceprint "选择赢取历装材料，且当日未获取"
        FW.SetTextView ("即时信息", "选择赢取历装材料，且当日未获取", 1400, 0, 520, 30)

        //ElseIf type = 1 and matchPointColor(480,1400,"5567BF",5) Then//选择收服支援，且未收服
    ElseIf type = 1  Then//有告别功能了，无须判断
        click 490, 1560//收服
        while not matchPointColor(538,574,"FFFFFF",5)//强度第一个星
            Delay 200
        Wend
        click 330, 1150
        Delay 300
        click 300,1200
        traceprint "选择收服支援"
        FW.SetTextView ("即时信息", "选择收服支援", 1400, 0, 520, 30)
    Else 
        click 1050,1860//关闭窗口
        traceprint "已赢取或收服，无法进入战斗"
        FW.SetTextView ("即时信息", "已赢取或收服，无法进入战斗", 1400, 0, 520, 30)
    End If

    Delay 300


End Function




Function fightLizhan(i)

    dim  looptime = 0
    While inFight() = False and looptime < 5
        looptime = looptime + 1
        click 1050,1860//关闭窗口
        Delay 400
        traceprint "点击并等待infight"
        FW.SetTextView ("即时信息", "点击并等待infight", 1400, 0, 520, 30)
    Wend
	
    If inFight() Then   //遇到战斗
        delay 200
        TracePrint "检测到战斗" 
        FW.SetTextView ("即时信息", "检测到战斗", 1400, 0, 520, 30)
        readyToFight 
		
        LizhanFight (i)
     
    End If
  
    If fightSettlement() Then //战斗结算时
        settlementOver
    End If
    
    Delay 300
    backWorld 
	
End Function

Function LizhanFight(i)
    readyToFight 
    // 1.瓦洛雷		2.恩波格洛	3.希亚特珀利斯	4.利布尔泰德	5.牧羊岩		6.桑谢德		7.库利亚布鲁克	8.克拉古斯比亚
    // 1.斧*****		2.弓****		3.书**			4.枪*		5.剑*		6.扇**		7.杖**			8.匕*
	
    If i = 1 Then 
        Lizhanaxe 
    ElseIf i = 2 Then
        Lizhanbow 
    ElseIf i = 3 Then
        Lizhanbook
    ElseIf i = 4 Then
        Lizhanspear
    ElseIf i = 5 Then
        Lizhansword
    ElseIf i = 6 Then
        Lizhanfan
    ElseIf i = 7 Then
        Lizhancane
    ElseIf i = 8 Then
        Lizhandagger
    End If	
End Function

Function Lizhanaxe() //历战斧
    traceprint "历战斧" 
    If inFight() Then 
      
        skill 1, 1, 0
        skill 2, 2, 0
        skill 3, 2, 0
        skill 4, 1, 0
        roundOver 
      
        xskill 2, 3, 0    
        skill 3, 3, 0
        xskill 4, 2, 0 
        roundOver 
      
        skill 1, 2, 0
        xskill 2, 1, 0
        skill 3, 2, 0
        skill 4, 3, 0 
        fullbp
        roundOver 
      
        skill 1, 1, 0
        fullbp
        roundOver 
      
        While inFight()
            exchange
            fullbp
            roundOver 
        Wend
    End If
End Function

Function Lizhanbow()  //历战弓	
    traceprint "历战弓"
    If inFight() Then 
     
        skill 1, 2, 0
        skill 2, 2, 0
        skill 3, 1, 0
        skill 4, 1, 0
        roundOver 
      
        skill 1, 1, 0
        skill 2, 1, 0
        skill 4, 2, 0
        fullbp
        roundOver 
     
        While inFight()
            fullbp
            roundOver
        Wend
    End If
End Function

Function Lizhanbook() //历战书
    traceprint "历战书"
    If inFight() Then 
      
        skill 1, 2, 0
        skill 2, 3, 0
        skill 3, 3, 0
        skill 4, 3, 0
        roundOver 
      
        skill 1, 1, 0
        skill 2, 2, 0
        fullbp
        roundOver 
     
        While inFight()
            fullbp
            roundOver
        Wend
    End If
End Function

Function Lizhanspear() //历战枪
    traceprint "历战枪"
    If inFight() Then 
      
        skill 1, 1, 0
        skill 2, 3, 0
        skill 3, 1, 0
        skill 4, 1, 0
        roundOver 
     
        skill 1, 2, 0
        skill 2, 2, 0
        skill 4, 2, 0
        fullbp
        roundOver 
     
        While inFight()
            fullbp
            roundOver
        Wend
    End If
End Function

Function Lizhansword() //历战剑
    traceprint "历战剑"
    If inFight() Then 
        
        skill 1, 2, 0
        skill 2, 2, 0
        skill 3, 2, 0
        skill 4, 3, 0
        roundOver 
     
        skill 1, 3, 0
        skill 3, 1, 0
        fullbp
        roundOver 
      
        While inFight()
            fullbp
            roundOver
        Wend
    End If
End Function

Function Lizhanfan()  //历战扇
    traceprint "历战扇"
    If inFight() Then 
       
        xskill 1, 2, 0
        skill 2, 2, 0
        skill 3, 2, 0
        skill 4, 3, 0
        roundOver 
     
        skill 3, 1, 0
        fullbp
        roundOver 
     
        While inFight()
            fullbp
            roundOver
        Wend
    End If
End Function

Function Lizhancane() //历战杖
    traceprint "历战杖"
    If inFight() Then 
     
        skill 1, 2, 0
        skill 2, 3, 0
        skill 3, 3, 0
        skill 4, 3, 0
        roundOver 
      
        skill 1, 1, 0
        skill 2, 2, 0
        fullbp
        roundOver 
     
        While inFight()
            fullbp
            roundOver
        Wend
    End If
End Function

Function Lizhandagger() //历战匕
    traceprint "历战匕首"
    If inFight() Then 
      
        skill 1, 1, 0
        skill 2, 1, 0
        skill 3, 3, 0
        skill 4, 1, 0
        roundOver 
     
        skill 1, 2, 0
        skill 2, 3, 0
        fullbp
        roundOver 
      
        While inFight()
            fullbp
            roundOver
        Wend
    End If
End Function

Function dismissHelper
	
    backWorld 
	    
    While matchPointColor(1048, 41, "E9E9E9", 1) <> true
        click 180, 330	
    Wend
    traceprint "打开队伍"
    FW.SetTextView "即时信息", "打开队伍", 1400, 0, 520, 30
    	
    While not matchPointColor(272, 98, "FFFFFF", 1)
        Delay 200
        traceprint "等待队伍界面"
    Wend
    while image.ocrText(874,363,937,657,0,1) <> "支援者列表"
        slowClick 280,215//点击支援者
        traceprint "点击支援者按钮"
        FW.SetTextView "即时信息", "点击支援者按钮", 1400, 0, 520, 30
    wend
    Delay 400
    		
    While matchPointColor(678, 723, "FFFFFF", 20) or matchPointColor(678,740, "FFFFFF", 20) or matchPointColor(712,654, "FFFFFF", 20)
        Click 680, 1000
        traceprint "选中支援者"
        FW.SetTextView "即时信息", "选中支援者", 1400, 0, 520, 30
        While not matchPointColor(187, 1096, "715925", 20)
            Delay 200
            traceprint "等待告别按钮"
            FW.SetTextView "即时信息", "等待告别按钮", 1400, 0, 520, 30
        Wend
        Click 190, 1200
        traceprint "点击告别按钮"
        FW.SetTextView "即时信息", "点击告别按钮", 1400, 0, 520, 30
        While not matchPointColor(350, 1100, "715A25", 20)
            Delay 200
            traceprint "等待告别确认按钮"
            FW.SetTextView "即时信息", "等待告别确认按钮", 1400, 0, 520, 30
        Wend
        slowClick 360, 1200
        slowClick 350, 960
        traceprint "已确认告别"
        FW.SetTextView "即时信息", "已确认告别", 1400, 0, 520, 30
        slowClick 280, 215//点击支援者
			
    Wend
    delay 100
    slowClick 185, 730//点击关闭
    delay 250
    click 1050,1860//关闭窗口
		
    While inWorld() <> True
        Delay 200
        backWorld
    Wend

End Function


Function Campfire1(n)
    篝火1用时 = Round(TickCount() /60000,1)
    TracePrint "******************Campfire1Boss*******************"
    FW.SetTextView "即时信息", "Campfire1Boss", 1400, 0, 520, 30
    useTeam n
    //tpSleep 1
    backWorld
    openMap
    tpAnywhere (999)//目的地999追忆之塔

    moveMinimap 705, 874//走到追忆之塔入口火苗
    TracePrint"走到追忆之塔入口火苗"
    FW.SetTextView "即时信息", "走到追忆之塔入口火苗", 1400, 0, 520, 30
    slowClick 650, 960 //点击上方火苗
    slowClick 540, 1250 //点击战争的篝火
    TracePrint "进入战争的篝火"
    FW.SetTextView "即时信息", "进入战争的篝火", 1400, 0, 520, 30
    While inWorld() <> True
        click 1057, 1884
        delay 200
        TracePrint "点击并等待回到主界面"
        FW.SetTextView "即时信息", "点击并等待回到主界面", 1400, 0, 520, 30
    Wend

    fightCampfire1Boss

    //切换回初始队伍 
    If initialTeam <> -1 Then 
        useTeam initialTeam
    End If

End Function


Function fightCampfire1Boss()

    TracePrint"*********************************************尝试执行fightCamp1Boss**********************************************"

    mark = 0//用于标记已进入某个地图，从而：第一个地图入口在营地， 后续的moveminimap 入口坐标选地图之间的传送点

    for k = targetMap to 2//全打改8

        targetMap = k

        While inWorld() <> True
            click 1057, 1884
            delay 200
            TracePrint "点击并等待回到主界面"
            FW.SetTextView "即时信息", "点击并等待回到主界面", 1400, 0, 520, 30
        Wend

        moveMinimap Entry(targetMap,mark,0),Entry(targetMap,mark,1)
        TracePrint"-------------------------------到达篝火1 " & Camp1_Name(k) & "入口"
        FW.SetTextView "即时信息", "到达篝火1 " & Camp1_Name(k) & "入口", 1400, 0, 520, 30
        if mark = 0 then//在营地
            If k =1 or k = 2 Then 
                slowClick 650, 960//点击 上方火苗
            ElseIf  k =3 or k = 4 Then 
                slowClick 500, 1160 //点击 右侧火苗
            ElseIf  k =5 or k = 6 Then 
                slowClick 470,960//点击 下方火苗
            ElseIf  k =7 or k = 8 Then 
                slowClick 500,740//点击 左侧火苗	
            End If
        Else 
            slowClick 500,1160//点击 右侧火苗
        End If

        slowClick 450, 1250 //点击 是
        TracePrint"-------------------------------进入篝火1 " & Camp1_Name(k)
        FW.SetTextView "即时信息", "进入篝火1 " & Camp1_Name(k), 1400, 0, 520, 30
        mark = 1

        While inWorld() <> True
            click 1057, 1884
            delay 200
            TracePrint "点击并等待回到主界面"
            FW.SetTextView "即时信息", "点击并等待回到主界面", 1400, 0, 520, 30
        Wend
        For enum = 1 To Len(Camp1(k)) - 1
   
            click 874, 1618//打开小地图
            delay 300
            If matchPointColor(Camp1(k, enum, 0) + 20, Camp1(k, enum, 1), "A89768", 5) Then 
                TracePrint Camp1_Name(k) & "第" & enum & "个怪在目的地" & Camp1(k,enum,0) & "," & Camp1(k,enum,1)
                FW.SetTextView "即时信息",  Camp1_Name(k) & "第" & enum & "个怪在目的地" & Camp1(k,enum,0) & "," & Camp1(k,enum,1), 1400, 0, 520, 30
                //判断怪是否已经刷过了,实现回城休息后只跑图不跑空怪

                moveMinimap Camp1(k,enum,0),Camp1(k,enum,1)//去篝火1BOSS
                TracePrint"-------------------------------到达篝火1 " & Camp1_Name(k) & "第" & enum & "个怪，坐标" & Camp1(k,enum,0) & "," & Camp1(k,enum,1)
                FW.SetTextView "即时信息",  "到达篝火1 " & Camp1_Name(k) & "第" & enum & "个怪，坐标" & Camp1(k,enum,0) & "," & Camp1(k,enum,1), 1400, 0, 520, 30
   
                drag 300,300, 500,300//上滑进入战斗
                TracePrint "---------上滑进入战斗"  & Camp1_Name(k) & "第" & enum & "个怪，坐标" & Camp1(k,enum,0) & "," & Camp1(k,enum,1)
                FW.SetTextView "即时信息", "上滑进入战斗" & Camp1_Name(k) & "第" & enum & "个怪，坐标" & Camp1(k, enum, 0) & "," & Camp1(k, enum, 1), 1400, 0, 520, 30

                Dim loopTime = 0
                While inFight() = False and looptime < 20
                    Delay 200
                    loopTime = loopTime + 1
                Wend


                If inFight() Then   //遇到战斗
                    delay 200
                    TracePrint "检测到战斗"  
                    FW.SetTextView "即时信息", "检测到战斗", 1400, 0, 520, 30
                    readyToFight 

                    AutoSkill currentTeam, Camp1_Weak(k, enum)

                    //delay 2000//忘了为啥加的，先注释掉
                    If fightSettlement() Then //战斗结算时
                        settlementOver 
                    End If
                    Delay 300
        
                End If

                TracePrint Camp1_Name(j) & "第" & enum & "个怪" & "已完成,运行" & Round(TickCount() /60000,1) & "分钟"
                FW.SetTextView ("即时信息", Camp1_Name(j) & "第" & enum & "个怪" & "已完成,运行" & Round(TickCount() /60000,1) & "分钟", 1400, 0, 520, 30)


                backWorld

                If needRecover And inWorld() Then  //需要恢复时
                    TracePrint "尝试休息"
                    FW.SetTextView "即时信息", "尝试休息", 1400, 0, 520, 30
                    If recoverAll() = 1 Then  //回城休息后从头再来
    
                        backWorld
                        openMap
                        tpAnywhere (999)//目的地999追忆之塔

                        moveMinimap 705, 874//走到追忆之塔入口火苗
                        TracePrint"走到追忆之塔入口火苗"
                        FW.SetTextView "即时信息", "走到追忆之塔入口火苗", 1400, 0, 520, 30
                        slowClick 650, 960 //点击上方火苗
                        slowClick 540, 1250 //点击战争的篝火
                        TracePrint "进入战争的篝火"
                        FW.SetTextView "即时信息", "进入战争的篝火", 1400, 0, 520, 30
                        While inWorld() <> True
                            click 1057, 1884
                            delay 200
                            TracePrint "点击并等待回到主界面"
                            FW.SetTextView "即时信息", "点击并等待回到主界面", 1400, 0, 520, 30
                        Wend

                        fightCampfire1Boss
                        Exit Function
    
                    End If
                Else 
                    TracePrint "不需要休息"
                    FW.SetTextView "即时信息", "不需要休息", 1400, 0, 520, 30
                End If


            Else 
                TracePrint Camp1_Name(j) & "第" & enum & "个怪不在目的地" & Camp1(k,enum,0) & "," & Camp1(k,enum,1) & ",检测下一个坐标"
                FW.SetTextView ("即时信息", Camp1_Name(j) & "第" & enum & "个怪不在目的地" & Camp1(k,enum,0) & "," & Camp1(k,enum,1) & ",检测下一个坐标", 1400, 0, 520, 30)
            End If
        Next
    Next
    篝火1用时 = Round(TickCount() /60000,1) - 篝火1用时
    FW.SetTextView ("主窗口", "篝火 1 完成,用时" & 篝火1用时 & "分钟", 0, 0, 1400, 30)
End Function


Function Campfire2()
    TracePrint "******************Campfire2*******************"
    FW.SetTextView "即时信息", "Campfire2", 1400, 0, 520, 30
    篝火2用时 = Round(TickCount() /60000,1)
    targetMap = 6//从地图6开始顺时针跑
    //tpSleep 1


    backWorld
    openMap
    tpAnywhere (999)//目的地999追忆之塔

    moveMinimap 705, 874//走到追忆之塔入口火苗
    TracePrint"走到追忆之塔入口火苗"
    FW.SetTextView "即时信息", "走到追忆之塔入口火苗", 1400, 0, 520, 30
    slowClick 650, 960 //点击上方火苗
    slowClick 375, 670 //点击战争的篝火2
    TracePrint "进入战争的篝火2"
    FW.SetTextView "即时信息", "进入战争的篝火2", 1400, 0, 520, 30
    While inWorld() <> True
        click 1057, 1884
        delay 200
        TracePrint "点击并等待回到主界面"
    Wend

    fightCampfire2 

    //切换回初始队伍 
    If initialTeam <> -1 Then 
        useTeam initialTeam
    End If

End Function



Function fightCampfire2()

    mark = 0//用于标记已进入某个地图，从而：第一个地图入口在营地， 后续的moveminimap 入口坐标选地图之间的传送点

    TracePrint"*********************************************尝试执行fightCamp2**********************************************"
    FW.SetTextView "即时信息", "尝试执行fightCamp2", 1400, 0, 520, 30
    dim j = 0//序号，用来辅助判断地图序号
    For j = targetMap To 13
        targetMap = j

        While inWorld() <> True
            click 1057, 1884
            delay 200
            TracePrint "点击并等待回到主界面"
        Wend

        moveMinimap Entry(targetMap,mark,0),Entry(targetMap,mark,1)
        TracePrint"-------------------------------到达篝火2 " & Camp2_Name(j) & "入口"
        FW.SetTextView "即时信息", "到达篝火2 " & Camp2_Name(j) & "入口", 1400, 0, 520, 30
        if mark = 0 then
            If j =1 or j = 2 Then 
                slowClick 650, 960//点击 上方火苗
            ElseIf  j =3 or j = 4 Then 
                slowClick 500, 1160 //点击 右侧火苗
            ElseIf  j =5 or j = 6 Then 
                slowClick 470,960//点击 下方火苗
            ElseIf  j =7 or j = 8 Then 
                slowClick 500,740//点击 左侧火苗	
            ElseIf j =9 or j = 10 Then 
                slowClick 650, 960//点击 上方火苗
            ElseIf  j =11 or j = 12 Then 
                slowClick 500, 1160 //点击 右侧火苗
            ElseIf j = 13 or j = 14 Then
                slowClick 470,960//点击 下方火苗
		
            End If
        Else 
            slowClick 500,1160//点击 右侧火苗
        End If
	
        slowClick 450, 1250 //点击 是
        TracePrint"-------------------------------进入篝火2 " & Camp2_Name(j)
        FW.SetTextView "即时信息", "进入篝火2 " & Camp2_Name(j), 1400, 0, 520, 30
        mark = 2
		
        While inWorld() <> True
            click 1057, 1884
            delay 200
            TracePrint "点击并等待回到主界面"
        Wend


        For enum = 1 To Len(Camp2(j)) - 1
            useTeam Camp2_Team(j, enum)

            click 874, 1618//打开小地图
            delay 300//避免小地图还没打开就执行下一步

            If matchPointColor(Camp2(j, enum, 0) + 60, Camp2(j, enum, 1), "A89768", 5) Or matchPointColor(Camp2(j, enum, 0) + 60, Camp2(j, enum, 1), "6190B3", 5) Then
		
                //判断怪是否已经刷过了,实现回城休息后只跑图不跑空怪
                TracePrint Camp2_Name(j) & "第" & enum & "个怪在目的地" & Camp2(j,enum,0) & "," & Camp2(j,enum,1)
                moveMinimap Camp2(j,enum,0),Camp2(j,enum,1)//走到怪前面
                TracePrint"-------------------------------到达篝火2 " & Camp2_Name(j) & " 第 " & enum & " 个怪，坐标" & Camp2(j,enum,0) & "," & Camp2(j,enum,1)
                FW.SetTextView "即时信息", "到达篝火2 " & Camp2_Name(j) & " 第 " & enum & " 个怪，坐标" & Camp2(j,enum,0) & "," & Camp2(j,enum,1), 1400, 0, 520, 30
                drag 300,300, 500,300//上滑进入战斗

                Dim loopTime = 0
                While inFight() = False and looptime < 20
                    Delay 200
                    loopTime = loopTime + 1
                Wend

                If inFight() Then //遇到战斗
                    delay 200
                    TracePrint "---------------检测到战斗：" & Camp2_Name(j) & "第" & enum & "个怪"
                    FW.SetTextView "即时信息", "检测到战斗：" & Camp2_Name(j) & "第" & enum & "个怪", 1400, 0, 520, 30
                    readyToFight 



                    //以下为篝火2的战斗指令--------------------------------------------------------------------------------------

                    If j = 6 and enum = 1 then//沙2boss 
                        resetEX 
                        Sskill 1, 2, 0
                        Sskill 2, 1, 0
                        Sskill 3, 1, 0
                        Sskill 4, 1, 0
                        roundOver 
      
                        Sskill 1, 3, 0
                        Sskill 3, 2, 0
                        Sskill 4, 2, 0
                        fullbp
                        roundOver 
      
      
                        While inFight()
                            exchange 
                            fullbp
                            roundOver 
                        Wend
                    ElseIf j = 6 and enum = 5 Then
       
                        AutoSkill currentTeam, Camp2_Weak(j, enum)
                        needRecover = True
     
                    ElseIf j = 7 and enum = 1 then //川2boss 
                        resetEX 
                        Sskill_target 1, 2, 0, "缇奇莲"
                        Sskill_target 6, 4, 0, "缇奇莲"
                        Sskill_target 3, 2, 0, "缇奇莲" 
                        Sskill_target 4, 2, 0, "缇奇莲"   
                        roundOver 
      
                        Sskill 3, 3, 0
                        fullbp
                        roundOver  
      
                        While inFight()
                            fullbp
                            roundOver 
                        Wend
        
                        needRecover = True
     
                    ElseIf j = 8 and enum = 1 then//崖2boss 
                        resetEX 
                        Sskill 1, 4, 0
                        Sskill 2, 2, 0
                        Sskill 3, 2, 0
                        Sskill 8, 2, 3
                        helper
                        roundOver  
        
                        Sskill 1, 3, 3
                        Sskill 3, 3, 0
                        Sskill 4, 3, 0
                        helper
                        roundOver 
      
                        Sskill 5, 1, 0
                        Sskill 2, 2, 2
                        Sskill 3, 1, 2
                        Sskill 4, 3, 3
                        roundOver 
      
                        Sskill 8, 5, 0
                        fullbp
                        roundOver 
        
                        While inFight() 
                            fullbp
                            roundOver 
                        Wend
        
                        needRecover = True
     
                    ElseIf j = 9 and enum = 1 Then//森2boss 
                        resetEX
                        Sskill 1, 2, 0
                        Sskill 2, 1, 2
                        Sskill 3, 1, 0
                        Sskill 4, 1, 0
                        roundOver
      
                        Sskill 1, 1, 0
                        Sskill 2, 2, 0
                        fullbp
                        roundOver 
      
                        While inFight() 
                            fullbp
                            roundOver 
                        Wend
        
                        needRecover = True
     
                    ElseIf j = 10 and enum = 1 then//雪2boss 
                        resetEX 
                        Sskill 1, 2, 0
                        Sskill 2, 1, 0
                        Sskill 3, 1, 0
                        Sskill 4, 1, 0
                        roundOver 
     
                        Sskill 1, 3, 0
                        Sskill 3, 2, 0
                        Sskill 4, 2, 0
                        fullbp
                        roundOver 
     
                        While inFight() 
                            fullbp
                            roundOver 
                        Wend
                    ElseIf j = 10 and enum = 2 Then //雪猫
                        While inFight()
                            exchange 
                            fullbp
                            roundOver 
                        Wend
                    ElseIf j = 10 and enum = 4 Then
		
                        AutoSkill currentTeam, Camp2_Weak(j, enum)
                        needRecover = True 
        
                    ElseIf j = 11 and enum = 1 then//平原2boss
                        resetEX 
                        Sskill 1, 2, 0
                        Sskill 2, 1, 0
                        Sskill 3, 2, 0
                        Sskill 4, 1, 0
                        roundOver
 	 
                        Sskill 1, 3, 1
                        Sskill 2, 1, 1
                        Sskill 3, 2, 1
                        Sskill 4, 1, 3
                        roundOver
 	 
                        Sskill 1, 1, 0
                        Sskill 2, 2, 0
                        Sskill 3, 3, 0
                        fullbp
                        roundOver
 	 
                        While inFight()
                            fullbp
                            roundOver 
                        Wend
                    ElseIf j = 11 and enum = 3 Then
		
                        AutoSkill currentTeam, Camp2_Weak(j, enum)
                        needRecover = True 
       
                    ElseIf j = 12 and enum = 1 then//海2boss 
                        resetEX 
                        Sskill 5, 2, 0
                        Sskill 2, 1, 2
                        Sskill 3, 1, 0
                        Sskill 4, 1, 0
                        roundOver
 	
                        Sskill 5, 3, 0
                        Sskill 2, 1, 0
                        Sskill 3, 1, 0
                        Sskill 4, 1, 0
                        fullbp
                        roundOver
      
                        Sskill 1, 1, 0
                        Sskill 2, 2, 0
                        fullbp
                        roundOver 
      
                        While inFight()
                            fullbp
                            roundOver 
                        Wend
                    ElseIf j = 12 and enum = 5 Then
		
                        AutoSkill currentTeam, Camp2_Weak(j, enum)
                        needRecover = True  
        
                    ElseIf j = 13 and enum = 1 then//山2boss  
                        exchange 
                        skill 1, 2, 0
                        skill 2, 2, 0
                        skill 3, 3, 0
                        skill 4, 2, 0
                        roundOver 
      
                        skill 1, 1, 0
                        xskill 4, 1, 0
                        roundOver 
      
                        skill 2, 1, 0
                        skill 4, 2, 0
                        fullbp
                        roundOver 
      
                        While inFight()
                            fullbp
                            roundOver 
                        Wend
                    ElseIf j = 13 and enum = 2 then//
                        resetEX 
                        Sskill 5, 2, 3
                        Sskill 2, 2, 0
                        Sskill 3, 2, 0
                        Sskill 4, 3, 0
                        roundOver
 	
                        Sskill 1, 3, 0
                        roundOver
 	
                        Sskill 1, 3, 2
                        Sskill 2, 2, 2
                        Sskill 3, 2, 2
                        Sskill 4, 3, 2
                        roundOver 
      
                        fullbp 
                        roundOver 
 	
                        While inFight()
                            fullbp
                            roundOver 
                        Wend
                    Else
                        AutoSkill currentTeam, Camp2_Weak(j, enum)
                    End If
	
                    //以上为篝火2的战斗指令--------------------------------------------------------------------------------------	


                End If

                TracePrint "----------------------------" & Camp2_Name(j) & " 第 " & enum & " 个怪" & "已完成,运行" & Round(TickCount() /60000,1) & "分钟" 
                FW.SetTextView ("主窗口", Camp2_Name(j) & " 第 " & enum & " 个怪" & "已完成", 0, 0, 1400, 30)
                backWorld

                If needRecover And inWorld() Then  //需要恢复时
                    TracePrint "尝试休息"
                    If recoverAll() = 1 Then  //回城休息后从头再来
    			
                        backWorld
                        openMap
                        tpAnywhere (999)//目的地999追忆之塔

                        moveMinimap 705, 874//走到追忆之塔入口火苗
                        TracePrint"走到追忆之塔入口火苗"
                        FW.SetTextView "即时信息", "走到追忆之塔入口火苗", 1400, 0, 520, 30
                        slowClick 650, 960 //点击上方火苗
                        slowClick 375, 670 //点击战争的篝火2
                        TracePrint "进入战争的篝火2"
                        FW.SetTextView "即时信息", "进入战争的篝火2", 1400, 0, 520, 30
                        While inWorld() <> True
                            click 1057, 1884
                            delay 200
                            TracePrint "点击并等待回到主界面"
                        Wend
    			
                        fightCampfire2
                        Exit Function
                    End If
                Else 
                    TracePrint "不需要休息"
                    FW.SetTextView "即时信息", "不需要休息", 1400, 0, 520, 30
                End If
            Else
                TracePrint Camp2_Name(j) & " 第 " & enum & " 个怪不在目的地" & Camp2(j,enum,0) & "," & Camp2(j,enum,1) & ",检测下一个坐标"
                FW.SetTextView ("即时信息", Camp2_Name(j) & " 第 " & enum & " 个怪不在目的地" & Camp2(j,enum,0) & "," & Camp2(j,enum,1) & ",检测下一个坐标", 1400, 0, 520, 30)
            End If
        Next
    Next
    篝火2用时 = Round(TickCount() / 60000, 1) - 篝火2用时

    FW.SetTextView ("主窗口", "篝火完成,用时 " & 篝火1用时 + 篝火2用时 & " 分钟", 0, 0, 1400, 30)
End Function




Function 花田()

    花田用时 = Round(TickCount() /60000,1)
    dim 花田1 = false, 花田2 = false, looptime, l = 0

    backWorld

    click 874, 1618//打开小地图
    delay 300
    If Image.OcrText(950, 150, 1010, 350, 0, 1) <> "无名 小镇" Then 
        TracePrint Image.OcrText(950, 150, 1010, 350, 0, 1) & ",不在无名小镇"
        backWorld
        openMap
        tpTown 0
        TracePrint "传送到无名小镇"
        FW.SetTextView "即时信息", "传送到无名小镇", 1400, 0, 520, 30
    Else 
        backWorld
    End If 

    moveMinimap 750,630//走到花田中间


    //收取花田1
    While 花田1 = false
        click 550,800//点击花田1

        looptime = 0
        While Image.OcrText(410, 910, 450, 1000, 0, 1) <> "确定" and looptime < 10
            Delay 200
            looptime = looptime + 1
            traceprint "等待弹出确认窗口"
            FW.SetTextView "即时信息", "等待弹出确认窗口", 1400, 0, 520, 30
        Wend

        If looptime = 10 Then 
            花田1 = True
            TracePrint "--------------------------没收到花田1"
            FW.SetTextView "即时信息", "没收到花田1", 1400, 0, 520, 30
        End If

        If 花田1 = false Then 
            TracePrint "--------------------------采集中"
            FW.SetTextView "即时信息", "采集中", 1400, 0, 520, 30
            If Len(Image.OcrText(550, 1060, 600, 1100, 0, 1)) < 2 Then 
                TracePrint "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1)
                FW.SetTextView "即时信息", "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1), 1400, 0, 520, 30
                l = l + 1
                TracePrint"运行" & Round(TickCount() /60000,1) & "分钟," & "花田重启" & l & "次"
                FW.SetTextView "主窗口", "正在收取花田 1 。花田重启 " & l & " 次", 0, 0, 1400, 30
                restartGame
            Else 
                花田1 = True
                TracePrint "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1)
                FW.SetTextView "即时信息", "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1), 1400, 0, 520, 30
                click 430,960//点击确认收取	
                TracePrint "-----------------------------------------已收取花田1"
                FW.SetTextView ("主窗口", "已收取花田 1", 0, 0, 1400, 30)
            End If
        End If
    Wend




    //收取花田2
    While 花田2 = false
        click 550,1090//点击花田2

        looptime = 0
        While Image.OcrText(410, 910, 450, 1000, 0, 1) <> "确定" and looptime < 10
            Delay 200
            looptime = looptime + 1
            traceprint "等待弹出确认窗口"
            FW.SetTextView "即时信息", "等待弹出确认窗口", 1400, 0, 520, 30
        Wend

        If looptime = 10 Then 
            花田2 = True
            TracePrint "--------------------------没收到花田2"
            FW.SetTextView "即时信息", "没收到花田2", 1400, 0, 520, 30
        End If

        If 花田2 = false Then 
            TracePrint "--------------------------采集中"
            If Len(Image.OcrText(550, 1060, 600, 1100, 0, 1)) < 2 Then 
                TracePrint "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1)
                FW.SetTextView "即时信息", "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1), 1400, 0, 520, 30
                l = l + 1
                TracePrint"运行" & Round(TickCount() /60000,1) & "分钟," & "花田重启" & l & "次"
                FW.SetTextView ("主窗口", "正在收取花田 2 。花田已重启 " & l & " 次", 0, 0, 1400, 30)
                restartGame 
            Else 
                花田2 = True
                TracePrint "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1)
                FW.SetTextView "即时信息", "果实数量：" & Image.OcrText(550, 1060, 600, 1100, 0, 1), 1400, 0, 520, 30
                click 430,960//点击确认收取	
                TracePrint "----------------------------------------已收取花田2"
                FW.SetTextView ("即时信息", "已收取花田 2", 1400, 0, 520, 30)
            End If
        End If
    Wend
    花田用时 = Round(TickCount() /60000,1) - 花田用时
    TracePrint"--------------------------花田完成,用时" & 花田用时 & "分钟"
    FW.SetTextView ("主窗口", "花田完成,用时 " & 花田用时 & " 分钟，重启了 " & l & "次", 0, 0, 1400, 30)
End Function

Function 果炎()
    果炎用时 = Round(TickCount() /60000,1)
    dim 果炎果实 = false, looptime, l = 0
    backWorld
    openMap
    tpAnywhere 13//传送到圣树之泉
    moveMinimap 722, 677//走到果树边上
    //收取果炎
    While 果炎果实 = False

        click 450,562//点击果炎
        looptime = 0
        While Image.OcrText(410, 910, 450, 1000, 0, 1) <> "确定" and looptime < 10
            Delay 200
            looptime = looptime + 1
            traceprint "等待弹出确认窗口"
            FW.SetTextView "即时信息", "等待弹出确认窗口", 1400, 0, 520, 30
        Wend

        If looptime = 10 Then 
            果炎果实 = True
            traceprint "--------------------------没收到果炎果实"
            FW.SetTextView "即时信息", "没收到果炎果实" , 1400, 0, 520, 30
        End If

        if 果炎果实 = False then
            if Image.OcrText(550, 850, 600, 1140, 0, 1) = "果炎果实 X100" then
                traceprint "薅到果炎果实了：" & Image.OcrText(530, 830, 600, 1140, 0, 1)
                FW.SetTextView "即时信息", "薅到果炎果实了：" & Image.OcrText(550, 850, 600, 1140, 0, 1), 1400, 0, 520, 30
                click 430,960//点击确认收取	
                TracePrint "----------------------------------------------------------------已收取果炎果实"
                FW.SetTextView "即时信息", "已收果炎果实", 1400, 0, 520, 30
                果炎果实 = True
            Else
                traceprint "果树"  & "没薅到果炎果实：" & Image.OcrText(550, 850, 600, 1140, 0, 1)
                FW.SetTextView "即时信息", "果炎果实"  & "没薅到果炎果实：" & Image.OcrText(550, 850, 600, 1140, 0, 1), 1400, 0, 520, 30
                l = l + 1
                TracePrint "果炎果实已重启" & l & "次。当前正在收取果炎果实 " 
                FW.SetTextView "主窗口", "果炎果实已重启" & l & "次。当前正在收取果炎果实 " , 0, 0, 1400, 30
                restartGame
            End If
        End If
    Wend


    果炎果实 = Round(TickCount() /60000,1) - 果炎果实
    TracePrint"-----------------------------------------------------果炎完成,总用时" & Round(TickCount() /60000,1) & "分钟"
    FW.SetTextView ("主窗口", "果炎果实完成，用时 " & 果炎果实 & " 分钟，重启了 " & l & "次", 0, 0, 1400, 30)
End Function

Function 羊毛()
    羊毛用时 = Round(TickCount() /60000,1)
    dim l = 0
    dim 羊 = {{{0, 0}, {0, 0}},_
{{490, 480}, {410, 1045}},_
{{480, 555}, {490, 1025}},_
{{450, 600}, {490, 1050}},_
{{405, 505}, {485, 885}},_
{{410, 600}, {440, 1070}},_
{{405, 530}, {535, 890}}}
    dim 羊毛已收 = Array(False,False,False,False,False,False,False)

    backWorld 

    click 874, 1618//打开小地图
    delay 300
    If Image.OcrText(950, 150, 1010, 350, 0, 1) <> "无名 小镇" Then 
        TracePrint "当前地图：" & Image.OcrText(950, 150, 1010, 350, 0, 1) & ",不在无名小镇"
        FW.SetTextView "即时信息", "当前地图：" & Image.OcrText(950, 150, 1010, 350, 0, 1) & ",不在无名小镇", 1400, 0, 520, 30
        backWorld
        openMap
        tpTown 0
        TracePrint "传送到无名小镇"
        FW.SetTextView "即时信息", "传送到无名小镇", 1400, 0, 520, 30
    Else 
        backWorld
    End If 



    for s = 1 to 6

        moveMinimap 羊(s,0,0),羊(s,0,1)//走到羊


        While 羊毛已收(s) = False

            click 羊(s,1,0),羊(s,1,1)//点击羊

            dim looptime = 0
            While Image.OcrText(410, 910, 450, 1000, 0, 1) <> "确定" and looptime < 5
                Delay 300
                looptime = looptime + 1
                traceprint "等待弹出确认窗口"
                FW.SetTextView "即时信息", "等待弹出确认窗口", 1400, 0, 520, 30
            Wend

            If looptime = 5 Then 
                羊毛已收(s) = True
                traceprint "--------------------------没收到羊" & s
                FW.SetTextView "即时信息", "没收到羊" & s, 1400, 0, 520, 30
            End If

            if 羊毛已收(s) = False then
                if Image.OcrText(550, 860, 600, 1140, 0, 1) = "追忆的羊毛 X3" or Image.OcrText(530, 830, 600, 1140, 0, 1) = "追忆的羊驼毛 X3" then
                    traceprint "薅到3追忆羊毛了：" & Image.OcrText(530, 830, 600, 1140, 0, 1)
                    FW.SetTextView "即时信息", "薅到3追忆羊毛了：" & Image.OcrText(530, 830, 600, 1140, 0, 1), 1400, 0, 520, 30
                    click 430,960//点击确认收取	
                    TracePrint "----------------------------------------------------------------已收取羊" & s
                    FW.SetTextView "即时信息", "已收取羊" & s, 1400, 0, 520, 30
                    羊毛已收(s) = True
                Else
                    traceprint "羊" & s & "没薅到3追忆羊毛：" & Image.OcrText(530, 830, 600, 1140, 0, 1)
                    FW.SetTextView "即时信息", "羊" & s & "没薅到3追忆羊毛：" & Image.OcrText(530, 830, 600, 1140, 0, 1), 1400, 0, 520, 30
                    l = l + 1
                    TracePrint "羊毛已重启" & l & "次。当前正在收取羊 " & s
                    FW.SetTextView "主窗口", "羊毛已重启" & l & "次。当前正在收取羊 " & s, 0, 0, 1400, 30
                    restartGame
                End If
            End If


        Wend

    Next

    羊毛用时 = Round(TickCount() /60000,1) - 羊毛用时
    TracePrint"-----------------------------------------------------羊毛完成,总用时" & Round(TickCount() /60000,1) & "分钟"
    FW.SetTextView ("主窗口", "羊毛完成，用时 " & 羊毛用时 & " 分钟，重启了 " & l & "次", 0, 0, 1400, 30)
End Function


Function 一键收菜()
	

    backWorld 

    click 874, 1618//打开小地图
    delay 300
    If Image.OcrText(950, 150, 1010, 350, 0, 1) <> "无名 小镇" Then 
        TracePrint "不在无名小镇"
        backWorld
        openMap
        mapStandardization //先标准化方便传送操作
        slowClick 823, 1157

    Else 
        backWorld
        openMap 
        slowClick 530, 960//点击无名小镇
    End If


    If matchPointColor(130, 1335, "6F5823", 5) = True Then 
        slowClick 125,1425//点击道具回收
        Click 185,1200//点击是	
        traceprint "-----------------------------------------------------------------完成一键收菜"
        FW.SetTextView "主窗口", "完成一键收菜", 0, 0, 1400, 30
    End If

    backWorld
End Function



/*------------------------------------------------------------------------------------------*/
/*--------------------------------------基础操作--------------------------------------------*/
/*------------------------------------------------------------------------------------------*/


//启动游戏
Function startGame()
    If Sys.GetFront() = "com.netease.ma167" Then 
        app = "com.netease.ma167"//网易
        FW.SetTextView "即时信息", "读取到包名: " & app, 1400, 0, 520, 30
        Exit Function
    ElseIf Sys.GetFront() = "com.netease.ma167.bilibili" Then
        app = "com.netease.ma167.bilibili" //b服
        FW.SetTextView "即时信息", "读取到包名: " & app, 1400, 0, 520, 30
        Exit Function
    Else
        traceprint "大霸，启动!"
        FW.SetTextView ("主窗口", "大霸，启动!", 0, 0, 1400, 30)
        RunApp "com.netease.ma167"
        RunApp "com.netease.ma167.bilibili"
	    	
        dim looptime = 0
        While not inWorld() and looptime < 100
            click 350, 700
            Delay 200
            looptime = looptime + 1
            traceprint looptime
        Wend
    				
        app = Sys.GetFront()
        TracePrint("读取到包名: " & app)
        FW.SetTextView "即时信息", "读取到包名: " & app, 1400, 0, 520, 30
    		
        If looptime = 100 Then 
            restartGame
        End If
    		
        traceprint "进入游戏"
        FW.SetTextView "即时信息", "进入游戏", 1400, 0, 520, 30
    End If

End Function




//重启游戏
Function restartGame()
    traceprint "重启游戏"
    FW.SetTextView "即时信息", "重启游戏", 1400, 0, 520, 30
    KillApp app
    Delay 1000
    RunApp app
    

    dim looptime = 0
    While not inWorld() and looptime < 100
        click 350, 700
        Delay 200
        looptime = looptime + 1
        traceprint looptime
    Wend
    
    If looptime = 150 Then 
        restartGame
    End If
    traceprint "进入游戏"
    FW.SetTextView "即时信息", "进入游戏", 1400, 0, 520, 30
  
End Function


//点击操作
Function click(x,y)
    Touch x, y, 100
    Delay 500
End Function

//快点击操作
Function fastclick(x,y)
    Touch x, y, 100
    Delay 200
End Function


//慢点击操作
Function slowClick(x,y)
    Touch x, y, 100
    Delay 800
End Function

//稳定滑动操作
Function roll(x1,y1,x2,y2)
    TouchDown x1,y1
    Delay 500
    TouchMove x2, y2, 0, 200
    Delay 500
    TouchUp 
    Delay 500
End Function

//快滑动操作
Function fastroll(x1,y1,x2,y2)
    TouchDown x1,y1
    Delay 200
    TouchMove x2, y2, 0, 200
    Delay 200
    TouchUp 
    Delay 300
End Function

Function drag(x1,y1,x2,y2)
    TouchDown x1,y1
    Delay 500
    TouchMove x2, y2, 0, 200
    Delay 2000
    TouchUp
End Function


//点击图片
Function clickPic(x1,y1,x2,y2,Pic, dirc)
    Dim intX, intY
    FindPic x1,y1,x2,y2,"Attachment:" & Pic & ".png","000000",dirc,0.75,intX,intY
    If intX > -1 Then
        TracePrint intX & "," & intY
        click (x1+x2)/2,(y1+y2)/2
    End If
End Function


//某点颜色识别。x,y为该点位置,color为匹配颜色,range为定位范围
Function matchPointColor(x, y, color,range)
    Dim intX, intY
    FindColor x - range, y - range, x + range, y + range, color, 0, ambiguity, intX, intY
    //如果没有找到，intX和intY的值都会被置为-1
    If intX > -1 And intY > -1 Then
        matchPointColor = true
    End If
End Function

//判断游戏是否正在运行，可用于避免游戏崩溃导致while循环出现死循环
Function inGame() 
    If app=Sys.GetFront() Then 
        inGame = true
    Else 
        TracePrint "检测到游戏崩溃"
        FW.SetTextView "即时信息", "检测到游戏崩溃", 1400, 0, 520, 30
    End If
End Function


/*------------------------------------------------------------------------------------------*/
/*------------------------------------判断当前界面-------------------------------------------*/
/*------------------------------------------------------------------------------------------*/



//战斗中(是的话函数返1)
Function inFight()
    If (matchPointColor(980,1584, "000000",1) And matchPointColor(928,1582, "E7ECF0",1))_
     Or (matchPointColor(767,1584, "000000",1) And matchPointColor(715,1582, "E7ECF0",1))_
     Or (matchPointColor(554,1584, "000000",1) And matchPointColor(501,1582, "E7ECF0",1))_
     Or (matchPointColor(1019,1584, "000000",1) And matchPointColor(990,950, "DDE6EE",1))_
     Or (matchPointColor(1020,1550, "A26827",1) And matchPointColor(990,950, "DDE6EE",1)) Then
     
        //判定的是1-3号位的精力的标和职业标左上角的黑色。这样只有放必杀的时候识别不出战斗中了
        //增加了必杀的识别，准备完毕按钮+其他必杀黑色面板/1号必杀蓝色面板
        inFight = true
    Else 
        inFight = False
        //TracePrint "不在战斗中" 
        FW.SetTextView "即时信息", "不在战斗中", 1400, 0, 520, 30
    End If
End Function

 
//战斗结算(是的话函数返1)
Function fightSettlement()
    If matchPointColor(1022, 153, "E8EBF0",1) Then 
        fightSettlement = true
        //TracePrint "检测到在战斗结算"
        FW.SetTextView "即时信息", "检测到在战斗结算", 1400, 0, 520, 30
    Else 
        //TracePrint "不在战斗结算"
        FW.SetTextView "即时信息", "不在战斗结算", 1400, 0, 520, 30
    End If
End Function


//世界中，且人物停止移动(是的话函数返1)
Function inWorld()
    If matchPointColor(218,96,"F6F6F5",1)  Then //判定左下角菜单
        inWorld = true
        TracePrint "检测到在世界中"
        FW.SetTextView "即时信息", "检测到在世界中", 1400, 0, 520, 30
    Else 
        inWorld = False 
    End If
End Function


//地图中(是的话函数返1)
Function inMap()
    If matchPointColor(1041, 832, "3D6DAF",1) And matchPointColor(1037, 1144, "76AAD2",1) Then
        inMap = true
        TracePrint "检测到在地图中"
        FW.SetTextView "即时信息", "检测到在地图中", 1400, 0, 520, 30
    Else 
        TracePrint "不在地图中" 
        FW.SetTextView "即时信息", "不在地图中", 1400, 0, 520, 30
    End If
End Function


//回归世界，重启游戏时也可用
Function backWorld()
    TracePrint "*********************************************尝试执行backWorld**********************************************"
    dim looptime = 0
    While True
        TracePrint "********************判断当前页面************************"
        FW.SetTextView "即时信息", "判断当前页面", 1400, 0, 520, 30
        If Sys.GetFront()<>app Then //检测游戏是否健在
            traceprint "重启" & app
            FW.SetTextView "即时信息", "重启" & app, 1400, 0, 520, 30
            restartGame
        ElseIf inMap() Then
            traceprint "关闭地图"
            FW.SetTextView "即时信息", "关闭地图", 1400, 0, 520, 30
            closeMap 
        ElseIf inFight() Then
            run 
            Delay 200
            If Image.OcrText(335, 700, 370, 740, 0, 1) = "否" then
                click 350,1200//点击 是
            End If
            TracePrint "逃跑"
            FW.SetTextView "即时信息", "逃跑", 1400, 0, 520, 30
        ElseIf fightSettlement() Then
            traceprint "结算中"
            FW.SetTextView "即时信息", "结算中", 1400, 0, 520, 30
            settlementOver 
        ElseIf inWorld() Then
            TracePrint "已回到世界中"
            FW.SetTextView "即时信息", "已回到世界中", 1400, 0, 520, 30
            Exit Function
        Else 
            TracePrint"未知界面"
            FW.SetTextView "即时信息", "未知界面", 1400, 0, 520, 30
            click 1057,1884
            //ShowMessage "未知界面，正在尝试关闭当前界面"
        End If
        looptime = looptime + 1
        If looptime = 10 Then 
            restartGame
        End If
        Delay 1000
    Wend
End Function




/*------------------------------------------------------------------------------------------*/
/*-------------------------------------世界中操作--------------------------------------------*/
/*------------------------------------------------------------------------------------------*/



//水平来回移动
Function moveY()
    //TracePrint "********************尝试执行moveY*********************"
    If inWorld() Then
        TracePrint"水平来回移动中"
        FW.SetTextView "即时信息", "水平来回移动中", 1400, 0, 520, 30
        Swipe 570,454, 548,858
        Delay 1400
        Swipe 600,1241, 522,661
        Delay 1400
    End If
End Function

//水平来回移动
Function moveZ()
    //TracePrint "********************尝试执行moveZ*********************"
    If inWorld() Then
        TracePrint"水平来回移动中"
        FW.SetTextView "即时信息", "水平来回移动中", 1400, 0, 520, 30
        Swipe 570,454, 748,858
        Delay 1400
        Swipe 600,1241, 222,661
        Delay 1400
    End If
End Function


//检测角色是否在小地图x,y位置并前往(如果不在则自动前往该位置,在则返True)
Function whereMinimap(x, y)
    TracePrint "******************尝试执行whereMinimap*******************"
    If inWorld() Then 
        click 874, 1618
        If matchPointColor(x, y, "7ED5E2", 5) Then

            whereMinimap = True
            TracePrint "到达目的地"
            FW.SetTextView "即时信息", "到达目的地", 1400, 0, 520, 30
            click 1048, 1854
        Else 
            slowClick x, y//原本在End If后面。到达目的地后点击画面，点到了人物 所以挪到Else里面
        End If
        
    Else 
        TracePrint "不在世界中，无法打开小地图"
        FW.SetTextView "即时信息", "不在世界中，无法打开小地图", 1400, 0, 520, 30
    End If
End Function


Function moveMinimap(x, y)
    TracePrint "**************************尝试执行moveMinimap:"& x &","& y &"***************************"

    Dim loopTime=0
    While inWorld() = False
        click 1048, 1855
        TracePrint "------------------------------------点击右上角关闭窗口"
        Delay 200
        loopTime = loopTime + 1
        TracePrint"循环次数"&loopTime
        If loopTime > 30 Then //循环超过30次
            TracePrint "-----------------------------------------------------------请debug"
            FW.SetTextView "即时信息", "循环超过30次，请debug", 1400, 0, 520, 30
            stopFight
        End If       
    Wend
    
    While inGame() And Not whereMinimap(x, y)
        Delay 1000
    Wend
    TracePrint "已经移动至指定位置"
End Function


//野外利用小地图移动(移动至x,y)(遇到怪自动撤退)
Function moveMinimapRun(x, y)
    TracePrint "**************************尝试执行moveMinimapRun***************************"
    If inWorld() Then 
        While inGame() And Not whereMinimap(x, y)
            Delay 1000
            If inFight() Then 
                run 
            End If
        Wend
    Else 
        TracePrint "不在世界中，无法打开小地图"
        FW.SetTextView "即时信息", "不在世界中，无法打开小地图", 1400, 0, 520, 30
    End If
    TracePrint "已经移动至指定位置"
    FW.SetTextView "即时信息", "已经移动至指定位置", 1400, 0, 520, 30
End Function


//野外利用小地图移动(移动至x,y)(遇到怪自动杀)
Function moveMinimapKill(x, y)
    TracePrint "**************************尝试执行moveMinimapKill***************************"
    If inWorld() Then 
        While inGame() And Not whereMinimap(x, y)
            Delay 1000
            If inFight() Then 
                chooseFight
            End If 
            settlementOver
        Wend

    Else 
        TracePrint "不在世界中，无法打开小地图"
        FW.SetTextView "即时信息", "不在世界中，无法打开小地图", 1400, 0, 520, 30
    End If
    TracePrint "已经移动至指定位置"
    FW.SetTextView "即时信息", "已经移动至指定位置", 1400, 0, 520, 30
End Function


//打开地图
Function openMap()
    TracePrint "******************尝试执行openMap*******************"
    If inWorld() Then 
        TracePrint "执行"
        While inGame() And Not inMap()
            click 150, 1290
            Delay 1000
        Wend
        TracePrint "地图打开成功"
        FW.SetTextView "即时信息", "地图打开成功", 1400, 0, 520, 30
        
    Else 
        TracePrint "不在世界中，无法打开地图"
        FW.SetTextView "即时信息", "不在世界中，无法打开地图", 1400, 0, 520, 30
    End If
End Function


//世界中恢复状态(通行证专属)(次数可能归零,不建议使用)
Function recover()
    backWorld
    TracePrint "******************尝试执行recover*******************"
    FW.SetTextView "即时信息", "尝试执行recover", 1400, 0, 520, 30
    If inWorld() Then 
        TracePrint "执行恢复"
        FW.SetTextView "即时信息", "执行恢复", 1400, 0, 520, 30
        If matchPointColor(330, 1782, "2E2E30",1) Then 
            click 330, 1782
            click 351, 1197
            While inGame() And Not inWorld()
                Delay 1000
                click 351, 1197
            Wend
            TracePrint "恢复完毕"
            FW.SetTextView "即时信息", "恢复完毕", 1400, 0, 520, 30
        Else 
            TracePrint "恢复次数不够"
            FW.SetTextView "即时信息", "恢复次数不够", 1400, 0, 520, 30
        End If
    Else 
        TracePrint "不在世界中，无法恢复状态"
        FW.SetTextView "即时信息", "不在世界中，无法恢复状态", 1400, 0, 520, 30
    End If
End Function


//前往瓦洛雷旅馆睡觉(有通行证者不建议使用)
Function sleep()
    TracePrint "******************尝试执行sleep*******************"
    FW.SetTextView "即时信息", "尝试执行sleep", 1400, 0, 520, 30
    If inWorld() Then 	
        TracePrint "执行"
        openMap //打开地图
        tpTown(1) //传送至瓦洛雷
        click 785, 958 //点击旅馆
        While inGame() And Not matchPointColor(646, 1056, "4E5658",1)
            delay 1000
        Wend
        click 646, 1056 //点击旅馆老板
        Delay 1000
        click 322, 1198 //一直点跳过对话并确认睡觉
        click 322, 1198
        click 322, 1198
        While inGame() And Not inWorld() //不在地图中说明睡觉没成功，则等待
            Delay 1000
            click 322, 1198 //关闭睡觉成功对话框
        Wend
        TracePrint "睡觉成功"
        FW.SetTextView "即时信息", "睡觉成功", 1400, 0, 520, 30
    Else 
        TracePrint "不在世界中，无法前往旅馆睡觉"
        FW.SetTextView "即时信息", "不在世界中，无法前往旅馆睡觉", 1400, 0, 520, 30
    End If
End Function


//恢复状态(万能通用)(建议使用)(原地恢复反0,城镇恢复反1)
Function recoverAll()
    TracePrint "************************************尝试执行recoverAll*************************************"
    If inWorld() Then 
        TracePrint "执行恢复"
        needRecover=False
        If  matchPointColor(330,1782, "2F2F31",1) Then //有通行证恢复次数
            TracePrint "有恢复次数"
            FW.SetTextView "即时信息", "有恢复次数", 1400, 0, 520, 30
            recover
            recoverAll = 0
        Else 
            TracePrint "无恢复次数"
            FW.SetTextView "即时信息", "无恢复次数", 1400, 0, 520, 30
            sleep 
            recoverAll = 1
        End If	
    Else 
        TracePrint "不在世界中，无法恢复状态"
        FW.SetTextView "即时信息", "不在世界中，无法恢复状态", 1400, 0, 520, 30
    End If
End Function



/*------------------------------------------------------------------------------------------*/
/*-------------------------------------地图中操作--------------------------------------------*/
/*------------------------------------------------------------------------------------------*/


//地图标准化(方便后续操作)
Function mapStandardization()
    TracePrint "**************尝试执行mapStandardization***************"
    FW.SetTextView "即时信息", "尝试执行mapStandardization", 1400, 0, 520, 30
    
    If inMap() Then 
        TracePrint "执行"
        TracePrint "判断地图是否缩略状态"
        If Not matchPointColor(116,1812, "000000",1) Then //地图必须是缩略状态
            TracePrint "缩略地图"
            click 116,1812
        End If
        TracePrint "成功"
        roll 920, 171, 171, 1671
        roll 920, 171, 171, 1671 //地图要划到左上角
        TracePrint "划到左上角"
        roll 119, 1711, 861, 891 //从左上角划到中间
        TracePrint "划到中间"
        FW.SetTextView "即时信息", "mapStandardization完成", 1400, 0, 520, 30
    Else 
        TracePrint "不在地图中，无法标准化"
    End If
    
End Function


//传送至城镇
//0.无名小镇 1.瓦洛雷 2.恩波格洛 3.希亚特珀利斯 4.利布尔泰德 5.牧羊岩 6.桑谢德 7.库利亚布鲁克 8.克拉古斯比亚 9.弗雷姆葛雷兹 10.维克塔霍洛 11.多尼艾斯克
Function tpTown(n)
    TracePrint "************************************************尝试执行tpTown*************************************************"
    If inMap() Then 
        mapStandardization //先标准化方便传送操作
        Select Case n //选择传送编号
        Case 0 //无名小镇
            click 823, 1157
            TracePrint "无名小镇"
            FW.SetTextView "即时信息", "前往无名小镇", 1400, 0, 520, 30
        Case 1 //瓦洛雷
            click 859, 715
            TracePrint "瓦洛雷"
            FW.SetTextView "即时信息", "前往瓦洛雷", 1400, 0, 520, 30
        Case 2 //恩波格洛
            click 886, 1001
            TracePrint "恩波格洛"
            FW.SetTextView "即时信息", "前往恩波格洛", 1400, 0, 520, 30
        Case 3 //希亚特珀利斯
            click 764,1265
            TracePrint "希亚特珀利斯"
            FW.SetTextView "即时信息", "前往希亚特珀利斯", 1400, 0, 520, 30
        Case 4 //利布尔泰德
            click 418,1404
            TracePrint "利布尔泰德"
            FW.SetTextView "即时信息", "前往利布尔泰德", 1400, 0, 520, 30
        Case 5 //牧羊岩
            click 256, 1341
            TracePrint "牧羊岩"
            FW.SetTextView "即时信息", "前往牧羊岩", 1400, 0, 520, 30
        Case 6 //桑谢德
            click 185, 963
            TracePrint "桑谢德"
            FW.SetTextView "即时信息", "前往桑谢德", 1400, 0, 520, 30
        Case 7 //库利亚布鲁克
            click 302, 554
            TracePrint "库利亚布鲁克"
            FW.SetTextView "即时信息", "前往库利亚布鲁克", 1400, 0, 520, 30
        Case 8 //克拉古斯比亚
            click 561, 526
            TracePrint "克拉古斯比亚"
            FW.SetTextView "即时信息", "前往克拉古斯比亚", 1400, 0, 520, 30
        Case 9 //弗雷姆葛雷兹
            click 766, 991
            TracePrint "弗雷姆葛雷兹"
            FW.SetTextView "即时信息", "前往弗雷姆葛雷兹", 1400, 0, 520, 30
        Case 10 //维克塔霍洛
            slowClick 859, 715 //先点瓦洛雷
            click 753, 773
            TracePrint "维克塔霍洛"	
            FW.SetTextView "即时信息", "前往维克塔霍洛", 1400, 0, 520, 30
        Case 11 //多尼艾斯克
            slowClick 302, 554 //先点库里亚布鲁克
            click 157,868
            TracePrint "多尼艾斯克"
            FW.SetTextView "即时信息", "前往多尼艾斯克", 1400, 0, 520, 30
        Case 12 //伊·齐耳洛
            slowClick 302, 554 //先点库里亚布鲁克
            click 871,240
            TracePrint "伊·齐耳洛"
            FW.SetTextView "即时信息", "前往伊·齐耳洛", 1400, 0, 520, 30
			
			
        Case Else
            TracePrint "未知传送点"
            Goto unknown
        End Select
        Delay 800
        slowClick 126, 1615 //确认传送操作
        slowClick 350, 1198
        TracePrint "确认传送操作"
        While inGame() And Not inWorld() //确认是否传送至世界
            Delay 1000
            TracePrint "传送中"
        Wend
        TracePrint "传送成功"
        FW.SetTextView "即时信息", "传送成功", 1400, 0, 520, 30
    Else 
        TracePrint "不在地图中，无法传送"
        FW.SetTextView "即时信息", "不在地图中，无法传送", 1400, 0, 520, 30
    End If
    Rem unknown //未知传送点则退出地图
    closeMap
End Function




//传送至任意传送点(包括城镇和野外)
//x.无名小镇附近 1x.瓦洛雷 2x.恩波格洛 3x.希亚特珀利斯 4x.利布尔泰德 5x.牧羊岩 6x.桑谢德 7x.库利亚布鲁克 8x.克拉古斯比亚 9x.弗雷姆葛雷兹 10x.维克塔霍洛 11x.多尼艾斯克 12x.伊·齐耳洛
Function tpAnywhere(n) 
    If inMap() Then 
        TracePrint "************************************************尝试执行tpAnywhere"&n&"*************************************************"
        Dim 圣树之泉 = false
        mapStandardization //先标准化方便传送操作
		
        If n>=0 And n<10 //无名小镇附近
            slowClick 823, 1157 //点小镇
            slowClick 1050, 62 //后退
            slowClick 107, 1812 //放大地图
            TracePrint "打开无名小镇附近"
            Select Case n 
            Case 0 //无名小镇
                click 530, 958
                TracePrint "无名小镇"
				
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
        
        ElseIf n=13 //追忆之塔
            slowClick 823, 1157 //点小镇
            slowClick 1050, 62 //后退
            slowClick 107, 1812 //放大地图
            TracePrint "打开无名小镇附近"
            Delay 500
            slowClick 712,1115 //点圣树之泉

        ElseIf n=999 //追忆之塔
            slowClick 823, 1157 //点小镇
            slowClick 1050, 62 //后退
            slowClick 107, 1812 //放大地图
            TracePrint "打开无名小镇附近"
            Delay 500
            slowClick 650, 970 //点追忆之塔

        ElseIf n>=10 And n<20 //瓦洛雷附近
            slowClick 859, 715  
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开瓦洛雷附近"
            Select Case n 
            Case 10 //瓦洛雷
                click 530, 958
                TracePrint "瓦洛雷"
             
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
        
		
        ElseIf n>=20 And n<30 //恩波格洛附近
            slowClick 886,1001
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开恩波格洛附近"
            Select Case n 
            Case 20 //恩波格洛
                click 530, 958
                TracePrint "恩波格洛"
            Case 21
                click 808, 701
                TracePrint "雪林闲地"
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
        
		
        ElseIf n>=30 And n<40 //希亚特珀利斯附近
            slowClick 764,1265
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开希亚特珀利斯附近"
            Select Case n 
            Case 30 //希亚特珀利斯
                click 530, 958
                TracePrint "希亚特珀利斯"
					
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
        
		
        ElseIf n>=40 And n<50 //利布尔泰德附近
            slowClick 418,1404
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开利布尔泰德附近"
            Select Case n 
            Case 40 //利布尔泰德
                click 530, 958
                TracePrint "利布尔泰德"
            Case 41 //中津海
                click 510,400
                TracePrint "中津海"
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
        
		
        ElseIf n>=50 And n<60 //牧羊岩附近
            slowClick 256,1341 
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开牧羊岩附近"
            Select Case n 
            Case 50 //牧羊岩
                click 530, 958
                TracePrint "牧羊岩"
					
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
        
		
        ElseIf n>=60 And n<70 //桑谢德附近
            slowClick 185,963
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开桑谢德附近"
            Select Case n 
            Case 60 //桑谢德
                click 530, 958
                TracePrint "桑谢德"
				
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
        
		
        ElseIf n>=70 And n<80 //库利亚布鲁克附近
            slowClick 302,554
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开库利亚布鲁克附近"
            Select Case n 
            Case 70 //库利亚布鲁克
                click 530, 958
                TracePrint "库利亚布鲁克"
					
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
        
		
        ElseIf n>=80 And n<90 //克拉古斯比亚附近
            slowClick 561, 526
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开克拉古斯比亚附近"
            Select Case n 
            Case 80	//克拉古斯比亚
                click 530, 958
                TracePrint "克拉古斯比亚"
				
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
        
		
        ElseIf n>=90 And n<100 //弗雷姆葛雷兹附近
            slowClick 766, 991
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开弗雷姆葛雷兹附近"
            Select Case n
            Case 90 //弗雷姆葛雷兹
                click 530, 958
                TracePrint "弗雷姆葛雷兹"
            Case 91 //叹息冰窟
                click 566, 704
                TracePrint "叹息冰窟"
                FW.SetTextView "即时信息", "前往叹息冰窟", 1400, 0, 520, 30
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
            
        ElseIf n>=100 And n<110 //维克塔霍洛附近
            slowClick 859, 715 //先点瓦洛雷
            slowClick  753, 773 
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开维克塔霍洛附近"
            Select Case n
            Case 100 //维克塔霍洛
                click 530, 958
                TracePrint "维克塔霍洛"
            Case 101 //大树的露珠
                click 516,1268
                TracePrint "大树的露珠"
				
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
            
        ElseIf n>=110 And n<120 //多尼艾斯克附近
            slowClick 302, 554 //先点库里亚布鲁克
            slowClick  157,868
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开多尼艾斯克附近"
            Select Case n
            Case 110 //多尼艾斯克
                click 530, 958
                TracePrint "多尼艾斯克"
            Case 111 //雾明瀑布
                click 442,1258
                TracePrint "雾明瀑布"
				
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
            
        ElseIf n>=120 And n<130 //伊·齐耳洛附近
            slowClick 302, 554 //先点库里亚布鲁克
            slowClick  871,240
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开伊·齐耳洛附近"
            Select Case n
            Case 120 //伊·齐耳洛
                click 537,265
                TracePrint "伊·齐耳洛"
            Case 121 //针柱之洞
                click 394,641
                TracePrint "针柱之洞"
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
            
        ElseIf n>=130 And n<140 //斯弗拉塔尔加附近
            slowClick 185,963 //先点桑谢德
            slowClick  140,1057
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开斯弗拉塔尔加附近"
            Select Case n
            Case 130 //斯弗拉塔尔加
                click 291,957
                TracePrint "斯弗拉塔尔加"
            Case 131 //白砂岩窟
                click 486,973
                TracePrint "白砂岩窟"
            Case 132 //沙宫
                click 575,587
                TracePrint "授富砂宫"
                FW.SetTextView "即时信息", "前往授富砂宫", 1400, 0, 520, 30
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
            
        ElseIf n>=140 And n<150 //格兰波特附近
            slowClick 418,1404 //先点利布泰尔德
            slowClick 1050, 62
            slowClick 750,1850//点格兰波特
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开格兰波特附近"
            Select Case n 
            Case 140 //格兰波特
                click 515, 1862
                TracePrint "格兰波特"
            Case 141 //洞窟
                click 524, 1447
                TracePrint "洞窟"
            Case 142 //地下水道
                click 672, 1840
                TracePrint "地下水道"
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
            
        ElseIf n>=160 And n<170 //贝尔肯附近
            slowClick 256,1341 //先点牧羊岩
            TracePrint "先点牧羊岩"
            slowClick 1050, 62
            slowClick 110,1280//点击贝尔肯
            TracePrint "点击贝尔肯"
            slowClick 1050, 62
            slowClick 107, 1812
            TracePrint "打开贝尔肯附近"
            Select Case n 
            Case 160 //格兰波特
                click 237,749//热腾的泉窟
                TracePrint "热腾的泉窟"
                FW.SetTextView "即时信息", "前往热腾的泉窟", 1400, 0, 520, 30
            Case Else
                TracePrint "未知传送点"
                Goto unknown
            End Select
           
           
        Else
            TracePrint "未知传送点"
            Goto unknown
        End If
        
        Delay 800
        slowClick 126, 1615 //确认传送操作
        /*if 圣树之泉 = False then
            If Image.OcrText(644, 915, 683, 987, 0, 1) = "入口" Then 
                TracePrint "去圣树之泉"
                click 644,915//确认
                圣树之泉 = True
            Else 
                TracePrint "不是去圣树之泉"
                圣树之泉 = False
            End If
        End If*/
        slowclick 644,915
        slowClick 350, 1198
        TracePrint "确认传送操作"
        While inGame() And Not inWorld() //确认是否传送至世界
            Delay 1000
            TracePrint "传送中"
        Wend
        TracePrint "传送成功"
        FW.SetTextView "即时信息", "传送成功", 1400, 0, 520, 30
    Else 
        TracePrint "不在地图中，无法传送"
        FW.SetTextView "即时信息", "不在地图中，无法传送", 1400, 0, 520, 30
    End If
    Rem unknown //未知传送点则退出地图
    closeMap
End Function


//关闭地图
Function closeMap()
    TracePrint "******************尝试执行closeMap*******************"
    If inMap() Then
        click 1048, 1854
        While inGame() And Not inWorld() //确认是否传送至世界
            Delay 1000
            click 1048, 1854
            TracePrint "关闭地图"
        Wend
    End If
End Function



/*------------------------------------------------------------------------------------------*/
/*-------------------------------------战斗中判断--------------------------------------------*/
/*------------------------------------------------------------------------------------------*/



//正在回合结束中(是的话函数返True)
Function roundEnd()
    If inFight() Then 
        If Not matchPointColor(113,1888, "9C9C9C",1) Then 
            roundEnd = True
            //TracePrint "回合结束中，无法操作"
        Else 
            roundEnd = False
            //TracePrint "战斗中"
        End If
        
    End If
End Function


//正在选择技能(是的话函数返True)（用来防止卡在选择技能界面）
Function chooseSkill(n)
    TracePrint "判断"&n&"号位是否在使用技能"
    If inFight() Then 
        If matchPointColor(1236-215*n,1555, "854B09",1) Then 
            chooseSkill = True
            FW.SetTextView "即时信息", "正在选择技能", 1400, 0, 520, 30
            //TracePrint "正在选择技能"
        End If
    End If
End Function

 
//是否是猫(是的话函数返1)
Function fatCat()
    TracePrint "判断是否是猫"
    FW.SetTextView "即时信息", "判断是否是猫", 1400, 0, 520, 30
    If  matchPointColor(968,225, "773322",1) Or matchPointColor(968,225, "7B3421",1) or matchPointColor(974,196, "47419E",1)_
     or (matchPointColor(572,502, "DBDADB",1) and matchPointColor(566,400, "726BB7",1)) or (matchPointColor(968,225, "7B3421",1) and matchPointColor(974,196, "4A419C",1))_
     or (matchPointColor(968,225, "773322",1) and matchPointColor(974,196, "47419E",1)) Then  //战斗时间轴上55级肥猫手上的钻石蓝and披风红
        fatCat = True
        TracePrint "发现55猫了！"
        FW.SetTextView "即时信息", "发现55猫了！", 1400, 0, 520, 30
    End If
End Function
Function doubleCat()
    //TracePrint "判断是否是猫"
    FW.SetTextView "即时信息", "判断是否是猫", 1400, 0, 520, 30
    If matchPointColor(962,222,"B5E3DE",1)  Or matchPointColor(973,198, "87464C",1)_
     or (matchPointColor(962,222,"B1E2E2",1) and matchPointColor(962,982,"B1E2E2",1))_
     or (matchPointColor(962,222,"B5E3DE",1) and matchPointColor(962,982,"B5E3DE",1))Then //两只50级猫手上的袋子
        doubleCat = True
        //TracePrint "发现50猫了！"
        FW.SetTextView "即时信息", "发现50猫了！", 1400, 0, 520, 30
    End If
End Function


//判断n号位血量(绿血反0，黄血反1，红血反2,血量过低不显示血条/没人 反3)
Function hp(n)
    //TracePrint "判断"&n&"号位血量"
    FW.SetTextView "即时信息",  "判断"&n&"号位血量", 1400, 0, 520, 30
    hp=0
    If inFight() Then 
    
        if n <=4 then
    
            If matchPointColor(1178 - 215 * n,1582, "548654",1) or matchPointColor(1178 - 215 * n,1582, "C2DF6C",1) Then 
                //TracePrint n & " :绿血或有盾"
                hp = 0
            ElseIf matchPointColor(1178 - 215 * n,1582, "0093A0",1) Then 
                TracePrint n & " :黄血"
                FW.SetTextView "即时信息", n & " :黄血", 1400, 0, 520, 30
                hp = 1
            ElseIf matchPointColor(1178 - 215 * n,1582,"0000AE",1) Then 
                TracePrint n & " :红血"
                FW.SetTextView "即时信息", n & " :红血", 1400, 0, 520, 30
                hp = 2
            Else
                TracePrint n & " :1滴血/倒地/无角色"
                FW.SetTextView "即时信息", n & " :1滴血/倒地/无角色", 1400, 0, 520, 30
                hp = 3
            End If
        Else 
            If matchPointColor(1172-215*(n-4),1763, "548654",1) or matchPointColor(1172-215*(n-4),1763, "C2DF6C",1) Then 
                //TracePrint n & " :绿血或有盾"
                hp = 0
            ElseIf matchPointColor(1172-215*(n-4),1763, "0093A0",1) Then 
                TracePrint n & " :黄血"
                FW.SetTextView "即时信息", n & " :黄血", 1400, 0, 520, 30
                hp = 1
            ElseIf matchPointColor(1172-215*(n-4),1763,"0000AE",1) Then 
                TracePrint n & " :红血"
                FW.SetTextView "即时信息", n & " :红血", 1400, 0, 520, 30
                hp = 2
            Else
                TracePrint n & " :1滴血/倒地/无角色"
                FW.SetTextView "即时信息", n & " :1滴血/倒地/无角色", 1400, 0, 520, 30
                hp = 3
            End If
        End If        
        
    Else
        TracePrint "不在战斗中，无法查看血量！"
        FW.SetTextView "即时信息", "不在战斗中，无法查看血量！", 1400, 0, 520, 30
    End If
End Function


Function hp_Die()
    hp_Die = False
    If hpd(5) + hpd(6) + hpd(7) + hpd(8) > 0 Then 
        hp_Die = True
    End If
End Function


Function hpd(n)
    //TracePrint "判断"&n&"号位倒地"
    hpd=0
    If inFight() Then         
        If n<5 Then
            If matchPointColor(1178 - 215 * n,1501,"343434",1) Then //前排
                hpd = 1
                TracePrint "------------------"& n &" 号倒地"
                FW.SetTextView "即时信息", n &" 号倒地", 1400, 0, 520, 30
            Else 
                hpd = 0
                // TracePrint ""&n&"号hp正常"               
            End If
        End If
        If n>=5 Then
            If matchPointColor(1172-215*(n-4),1761,"1C1C1C",1) Then //后排
                hpd = 1
                TracePrint "------------------"& n &" 号倒地"
                FW.SetTextView "即时信息", n &" 号倒地", 1400, 0, 520, 30
            Else 
                hpd = 0
                //TracePrint ""&n&"号hp正常"   
            End If
        End If        
    Else 
        //TracePrint "不在战斗中，无法查看hp！"
    End If
End Function
 
 
//判断n号位精力百分比
Function spPercent(n)
    //TracePrint "判断"&n&"号位精力"
    
    dim spPercent=0,s

    If inFight() Then 
        If n<5 Then//前排
            for s = 0 to 150 step 15
                If matchPointColor(1135 - 215 * n, 1575 + s, "867954", 1) = True Then 
                    spPercent = round(s/1.5,0)
                End If
            Next

        End If

        If n >= 5 Then //后排
            for s = 0 to 110 step 11
                If matchPointColor(1137 - 215 * (n - 4), 1758 + s, "867954", 1) = True Then 
                    spPercent = round(s/1.1,0)
                End If
            Next

        End If
    Else 
        TracePrint "不在战斗中，无法查看精力！"
    End If
End Function
 
 
 
//判断n号位精力(比较低时(约35%)反1)
Function sp(n)
    //TracePrint "判断"&n&"号位精力"
    
    sp=0
    If inFight() Then 
        If n<5 Then
            If matchPointColor(1135-215*n,1615,"867954",1) Then //前排
                sp = 0
                //TracePrint n & "有精力"
            Else 
                sp = 1
                TracePrint n & ":精力低"
                FW.SetTextView "即时信息", n & ":精力低", 1400, 0, 520, 30
            End If
        End If
        If n>=5 Then
            If matchPointColor(1136-215*(n-4),1787,"867954",1) Then //后排
                sp = 0
                //TracePrint n & "有精力"
            Else 
                sp = 1
                TracePrint n & ":精力低"
                FW.SetTextView "即时信息", n & ":精力低", 1400, 0, 520, 30
            End If
        End If
    Else 
        //TracePrint "不在战斗中，无法查看精力！"
    End If
End Function



 
 
/*------------------------------------------------------------------------------------------*/
/*-------------------------------------战斗中操作--------------------------------------------*/
/*------------------------------------------------------------------------------------------*/
 
//释放技能 (第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个)
Function skill(a, b, c)
    TracePrint "******************尝试执行skill*******************"
    dim looptime = 0
    If inFight() Then 
        TracePrint a & "号位释放" & b & "技能，消耗" & c & "bp"
        FW.SetTextView "即时信息", a & "号位释放" & b & "技能，消耗" & c & "bp", 1400, 0, 520, 30
        Click 962 - (a - 1) * 214, 1603//选人
        delay 100
        rem skl
        If c=0 And b<>5 Then //不用bp且不用绝招时，点技能
            click 780 - 160 * b, 1200
        ElseIf b=5 Then //用绝招时
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
        Else //用bp时，拖动技能
            roll 780 - 160 * b, 1419, 780 - 160 * b, 1419 + c * 140
        End If
        
        While inGame() And chooseSkill(a)
            //click 909,788 //点一下防止技能没放出来导致卡住
            fastclick 1060,400//修改点击位置，大型怪（篝火1川boss （基加提亚斯异种））在909,788点一下不能能关闭选技能界面
        Wend

        If b <> 0 and image.ocrText(875 - (a - 1) * 214, 1600, 905 - (a - 1) * 214, 1655, 0, 1) = "战斗" and looptime < 3 Then 
            looptime = looptime + 1
            Click 962 - (a - 1) * 214, 1603//选人
            delay 100
            goto skl//技能没选上时重新选一次
        End If

    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function


//换人释放技能 (第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个)
Function xskill(a, b, c)
    TracePrint "******************尝试执行xskill******************"
    dim looptime = 0
    If inFight() Then 
        TracePrint a+4 & "号位释放" & b & "技能，消耗" & c & "bp"
        FW.SetTextView "即时信息", a + 4 & "号位释放" & b & "技能，消耗" & c & "bp", 1400, 0, 520, 30
        Click 962 - (a - 1) * 214, 1603//选人
        Click 122, 1707//交替
        Delay 100
        rem skl
        If c=0 And b<>5 Then //不用bp且不用绝招时，点技能 
            click 780 - 160 * b, 1200
        ElseIf b=5 Then //用绝招时
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
        Else //用bp时，拖动技能
            roll 780 - 160 * b, 1419, 780 - 160 * b, 1419 + c * 140
        End If
        
        While inGame() And chooseSkill(a)
            fastclick 1060,400//点一下防止技能没放出来导致卡住
        Wend

        If b <> 0 and image.ocrText(875 - (a - 1) * 214, 1600, 905 - (a - 1) * 214, 1655, 0, 1) = "战斗" and looptime < 3 Then 
            looptime = looptime + 1
            Click 962 - (a - 1) * 214, 1603//选人。人已经换了所以点选即可
            delay 100
            goto skl//技能没选上时重新选一次
        End If

    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function
 
 
//万能使用技能(第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个)
//(根据初始编队使用技能，比如5号位是EX洁哥，Sskill会一直使用EX洁，自动切换前后排)
Function Sskill(a, b, c)
 	
    //TracePrint "******************尝试执行Sskill******************"
    If (a = 1 And EX1) Or (a = 5 And Not EX1) Then //1号位需要换人
        xskill 1, b, c
        EX1=Not EX1
    ElseIf (a = 2 And EX2) Or (a = 6 And Not EX2) Then //2号位需要换人
        xskill 2, b, c
        EX2=Not EX2
    ElseIf (a = 3 And EX3) Or (a = 7 And Not EX3) Then //3号位需要换人
        xskill 3, b, c
        EX3=Not EX3
    ElseIf (a = 4 And EX4) Or (a = 8 And Not EX4) Then //4号位需要换人
        xskill 4, b, c
        EX4=Not EX4
    ElseIf (a = 5 And EX1) Or (a = 1 And Not EX1) Then 
        skill 1, b, c
    ElseIf (a = 6 And EX2) Or (a = 2 And Not EX2) Then 
        skill 2, b, c
    ElseIf (a = 7 And EX3) Or (a = 3 And Not EX3) Then 
        skill 3, b, c	
    ElseIf (a = 8 And EX4) Or (a = 4 And Not EX4) Then 
        skill 4, b, c		
    End If
End Function

 

 
/*-------------------------------------选人释放技能--------------------------------------------*/

Function selectEnemy(d)
    If IsNumeric(d) = False or d = 0 Then 
        TracePrint "选择攻击对象"
        Select Case d
            //
        Case "缇奇莲"
            click 540, 200
        Case "缇奇莲上"
            click 570, 700
        Case "缇奇莲下"
            click 430, 460
            //
        Case "戈洛萨姆"
            click 540, 200
        Case "戈洛萨姆上"
            click 570, 700
        Case "戈洛萨姆下"
            click 430, 460
            //
        Case "瓦尔坎"
            click 535, 190
        Case "瓦尔坎上"
            click 575, 700
        Case "瓦尔坎下"
            click 400, 450
            //
        Case "利杜"
            click 540, 200
        Case "利杜上"
            click 570, 700
        Case "利杜下"
            click 430, 460
            //
        case 0 
            click 540, 200
        End Select
    End If
End Function

Function selectPartner(d)
    If IsNumeric(d) and d >= 1 and d <= 4 Then 
        TracePrint "选择救援队友: " & d
        click 1175 - 215 * d, 1620
    ElseIf IsNumeric(d) and d >= 5 and d <= 8 Then
        TracePrint "选择救援队友: " & d
        click 1175 - 215 * (d - 4), 1800
    End If
End Function
 
 
//释放技能,选择目标(第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个,施法对象d)
Function skill_target(a, b, c, d)
    TracePrint "******************尝试执行skill_target*******************"
    dim looptime = 0
    If inFight() Then 
        TracePrint a & "号位释放" & b & "技能，消耗" & c & "bp，施法对象: " & d
        FW.SetTextView "即时信息", a & "号位释放" & b & "技能，消耗" & c & "bp", 1400, 0, 520, 30
        Click 962 - (a - 1) * 214, 1603//选人
        selectEnemy(d)//选择攻击对象
        Rem skl

        If c=0 And b<>5 Then //不用bp且不用绝招时，点技能
            click 780 - 160 * b, 1200
        ElseIf b=5 Then //用绝招时
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
        Else //用bp时，拖动技能
            roll 780 - 160 * b, 1419, 780 - 160 * b, 1419 + c * 140
        End If
        selectPartner (d)//选择救援队友
        
        While inGame() And chooseSkill(a)
            fastclick 1060,400//点一下防止技能没放出来导致卡住
        Wend

        If b <> 0 and image.ocrText(875 - (a - 1) * 214, 1600, 905 - (a - 1) * 214, 1655, 0, 1) = "战斗" and looptime < 3 Then 
            looptime = looptime + 1
            Click 962 - (a - 1) * 214, 1603//选人
            delay 100
            goto skl//技能没选上时重新选一次
        End If

    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function


//换人释放技能,选择目标(第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个,施法对象d)
Function xskill_target(a, b, c, d)
    TracePrint "******************尝试执行xskill_target******************"
    dim looptime = 0
    If inFight() Then 
        TracePrint a+4 & "号位释放" & b & "技能，消耗" & c & "bp，施法对象: " & d
        FW.SetTextView "即时信息", a + 4 & "号位释放" & b & "技能，消耗" & c & "bp", 1400, 0, 520, 30
        Click 962 - (a - 1) * 214, 1603//选人
        Click 122, 1707//交替
        selectEnemy(d)//选择攻击对象
        rem skl  
        If c=0 And b<>5 Then //不用bp且不用绝招时，点技能 
            click 780 - 160 * b, 1200
        ElseIf b=5 Then //用绝招时
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
        Else //用bp时，拖动技能
            roll 780 - 160 * b, 1419, 780 - 160 * b, 1419 + c * 140
        End If
        selectPartner (d)//选择救援队友
        
        While inGame() And chooseSkill(a)
            fastclick 1060,400//点一下防止技能没放出来导致卡住
        Wend

        If b <> 0 and image.ocrText(875 - (a - 1) * 214, 1600, 905 - (a - 1) * 214, 1655, 0, 1) = "战斗" and looptime < 3 Then 
            looptime = looptime + 1
            Click 962 - (a - 1) * 214, 1603//选人。人已经换了所以点选即可
            delay 100
            goto skl//技能没选上时重新选一次
        End If  
    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function


//万能使用技能,选择目标(第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个,施法对象d)
//(根据初始编队使用技能，比如5号位是EX洁哥，Sskill会一直使用EX洁，自动切换前后排)
Function Sskill_target(a, b, c, d)

    //TracePrint "******************尝试执行Sskill_target******************"
    If (a = 1 And EX1) Or (a = 5 And Not EX1) Then //1号位需要换人
        xskill_target 1, b, c, d
        EX1=Not EX1
    ElseIf (a = 2 And EX2) Or (a = 6 And Not EX2) Then //2号位需要换人
        xskill_target 2, b, c, d
        EX2=Not EX2
    ElseIf (a = 3 And EX3) Or (a = 7 And Not EX3) Then //3号位需要换人
        xskill_target 3, b, c, d
        EX3=Not EX3
    ElseIf (a = 4 And EX4) Or (a = 8 And Not EX4) Then //4号位需要换人
        xskill_target 4, b, c, d
        EX4=Not EX4
    ElseIf (a = 5 And EX1) Or (a = 1 And Not EX1) Then 
        skill_target 1, b, c, d
    ElseIf (a = 6 And EX2) Or (a = 2 And Not EX2) Then 
        skill_target 2, b, c, d
    ElseIf (a = 7 And EX3) Or (a = 3 And Not EX3) Then
        skill_target 3, b, c, d	
    ElseIf (a = 8 And EX4) Or (a = 4 And Not EX4) Then 
        skill_target 4, b, c, d	
    End If
End Function


/*------------------------------------------------------------------------------------------*/
/*-------------------------------------自动放大招--------------------------------------------*/
/*------------------------------------------------------------------------------------------*/

//释放技能 (第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个)
Function skill_Ulti(a, b, c)
    TracePrint "******************尝试执行skill_Ulti*******************"
    dim looptime = 0
    If inFight() Then 
        TracePrint a & "号位释放" & b & "技能，消耗" & c & "bp"
        FW.SetTextView "即时信息", a & "号位释放" & b & "技能，消耗" & c & "bp", 1400, 0, 520, 30
        
        Click 962 - (a - 1) * 214, 1603//选人
        rem skl
        If matchPointColor(869, 1018, "3196FE", 3) <> True and matchPointColor(869, 1018, "3F3F3F", 3) <> True Then 
            //必杀条颜色变亮，放必杀。3F3F3F是放必杀后的灰色
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
            
        ElseIf c=0 And b<>5 Then //不用bp且不用绝招时，点技能
            click 780 - 160 * b, 1200
        ElseIf b=5 Then //用绝招时
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
        Else //用bp时，拖动技能
            roll 780 - 160 * b, 1419, 780 - 160 * b, 1419 + c * 140
        End If
        
        While inGame() And chooseSkill(a)
            //click 909,788 //点一下防止技能没放出来导致卡住
            fastclick 1060,400//修改点击位置，大型怪（篝火1川boss （基加提亚斯异种））在909,788点一下不能能关闭选技能界面
        Wend

        If b <> 0 and image.ocrText(875 - (a - 1) * 214, 1600, 905 - (a - 1) * 214, 1655, 0, 1) = "战斗" and looptime < 3 Then 
            looptime = looptime + 1
            Click 962 - (a - 1) * 214, 1603//选人
            Delay 100
            goto skl//技能没选上时重新选一次
        End If
  
    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function


//换人释放技能 (第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个)
Function xskill_Ulti(a, b, c)
    TracePrint "******************尝试执行xskill_Ulti******************"
    dim looptime = 0
    If inFight() Then 
        TracePrint a+4 & "号位释放" & b & "技能，消耗" & c & "bp"
        FW.SetTextView "即时信息", a + 4 & "号位释放" & b & "技能，消耗" & c & "bp", 1400, 0, 520, 30
        Click 962 - (a - 1) * 214, 1603//选人
        Click 122, 1707//交替
        rem skl
        If matchPointColor(869, 1018, "3196FE", 3) <> True and matchPointColor(869, 1018, "3F3F3F", 3) <> True Then 
            //必杀条颜色变亮，放必杀。3F3F3F是放必杀后的灰色
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
            
        ElseIf c=0 And b<>5 Then //不用bp且不用绝招时，点技能 
            click 780 - 160 * b, 1200
        ElseIf b=5 Then //用绝招时
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
        Else //用bp时，拖动技能
            roll 780 - 160 * b, 1419, 780 - 160 * b, 1419 + c * 140
        End If
        
        While inGame() And chooseSkill(a)
            fastclick 1060,400//点一下防止技能没放出来导致卡住
        Wend

        If b <> 0 and image.ocrText(875 - (a - 1) * 214, 1600, 905 - (a - 1) * 214, 1655, 0, 1) = "战斗" and looptime < 3 Then 
            looptime = looptime + 1
            Click 962 - (a - 1) * 214, 1603//选人。人已经换了所以点选即可
            delay 100
            goto skl//技能没选上时重新选一次
        End If

    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function
 
 
//万能使用技能(第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个)
//(根据初始编队使用技能，比如5号位是EX洁哥，Sskill会一直使用EX洁，自动切换前后排)
Function Sskill_Ulti(a, b, c)
 	
    //TracePrint "******************尝试执行Sskill_Ulti******************"
    If (a = 1 And EX1) Or (a = 5 And Not EX1) Then //1号位需要换人
        xskill_Ulti 1, b, c
        EX1=Not EX1
    ElseIf (a = 2 And EX2) Or (a = 6 And Not EX2) Then //2号位需要换人
        xskill_Ulti 2, b, c
        EX2=Not EX2
    ElseIf (a = 3 And EX3) Or (a = 7 And Not EX3) Then //3号位需要换人
        xskill_Ulti 3, b, c
        EX3=Not EX3
    ElseIf (a = 4 And EX4) Or (a = 8 And Not EX4) Then //4号位需要换人
        xskill_Ulti 4, b, c
        EX4=Not EX4
    ElseIf (a = 5 And EX1) Or (a = 1 And Not EX1) Then 
        skill_Ulti 1, b, c
    ElseIf (a = 6 And EX2) Or (a = 2 And Not EX2) Then 
        skill_Ulti 2, b, c
    ElseIf (a = 7 And EX3) Or (a = 3 And Not EX3) Then 
        skill_Ulti 3, b, c	
    ElseIf (a = 8 And EX4) Or (a = 4 And Not EX4) Then 
        skill_Ulti 4, b, c		
    End If
End Function

 


//释放技能,选择目标(第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个,施法对象d)
Function skill_target_Ulti(a, b, c, d)
    TracePrint "******************尝试执行skill_target_Ulti*******************"
    dim looptime = 0
    If inFight() Then 
        TracePrint a & "号位释放" & b & "技能，消耗" & c & "bp，施法对象: " & d
        FW.SetTextView "即时信息", a & "释放" & b & "技能，消耗" & c & "bp，对象: " & d, 1400, 0, 520, 30
        Click 962 - (a - 1) * 214, 1603//选人
        selectEnemy(d)//选择攻击对象
        rem skl
        If matchPointColor(869, 1018, "3196FE", 3) <> True and matchPointColor(869, 1018, "3F3F3F", 3) <> True Then 
            //必杀条颜色变亮，放必杀。3F3F3F是放必杀后的灰色
            Click 950, 1050
            Click 350, 1400
            delay 200
            click 1060,400
            
        ElseIf c=0 And b<>5 Then //不用bp且不用绝招时，点技能
            click 780 - 160 * b, 1200
        ElseIf b=5 Then //用绝招时
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
        Else //用bp时，拖动技能
            roll 780 - 160 * b, 1419, 780 - 160 * b, 1419 + c * 140
        End If
        selectPartner (d)//选择救援队友
        
        While inGame() And chooseSkill(a)
            fastclick 1060,400//点一下防止技能没放出来导致卡住
        Wend

        If b <> 0 and image.ocrText(875 - (a - 1) * 214, 1600, 905 - (a - 1) * 214, 1655, 0, 1) = "战斗" and looptime < 3 Then 
            looptime = looptime + 1
            Click 962 - (a - 1) * 214, 1603//选人
            delay 100
            goto skl//技能没选上时重新选一次
        End If

    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function


//换人释放技能,选择目标(第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个,施法对象d)
Function xskill_target_Ulti(a, b, c, d)
    TracePrint "******************尝试执行xskill_target_Ulti******************"
    dim looptime = 0
    If inFight() Then 
        TracePrint a+4 & "号位释放" & b & "技能，消耗" & c & "bp，施法对象: " & d
        FW.SetTextView "即时信息", a + 4 & "释放" & b & "技能，消耗" & c & "bp，对象: " & d, 1400, 0, 520, 30
        Click 962 - (a - 1) * 214, 1603//选人
        Click 122, 1707//交替
        selectEnemy(d)//选择攻击对象
        rem skl
        If matchPointColor(869, 1018, "3196FE", 3) <> True and matchPointColor(869, 1018, "3F3F3F", 3) <> True Then 
            //必杀条颜色变亮，放必杀。3F3F3F是放必杀后的灰色
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
            
        ElseIf c=0 And b<>5 Then //不用bp且不用绝招时，点技能 
            click 780 - 160 * b, 1200
        ElseIf b=5 Then //用绝招时
            Click 950, 1050
            //Click 350, 1400//未带支炎兽必杀位置
            Click 300, 1400//带支炎兽必杀位置
            delay 200
            click 1060,400
        Else //用bp时，拖动技能
            roll 780 - 160 * b, 1419, 780 - 160 * b, 1419 + c * 140
        End If
        selectPartner (d)//选择救援队友
        
        While inGame() And chooseSkill(a)
            fastclick 1060,400//点一下防止技能没放出来导致卡住
        Wend

        If b <> 0 and image.ocrText(875 - (a - 1) * 214, 1600, 905 - (a - 1) * 214, 1655, 0, 1) = "战斗" and looptime < 3 Then 
            looptime = looptime + 1
            Click 962 - (a - 1) * 214, 1603//选人。人已经换了所以点选即可
            delay 100
            goto skl//技能没选上时重新选一次
        End If

    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function


//万能使用技能,选择目标(第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个,施法对象d)
//(根据初始编队使用技能，比如5号位是EX洁哥，Sskill会一直使用EX洁，自动切换前后排)
Function Sskill_target_Ulti(a, b, c, d)

    //TracePrint "******************尝试执行Sskill_target_Ulti******************"
    If (a = 1 And EX1) Or (a = 5 And Not EX1) Then //1号位需要换人
        xskill_target_Ulti 1, b, c, d
        EX1=Not EX1
    ElseIf (a = 2 And EX2) Or (a = 6 And Not EX2) Then //2号位需要换人
        xskill_target_Ulti 2, b, c, d
        EX2=Not EX2
    ElseIf (a = 3 And EX3) Or (a = 7 And Not EX3) Then //3号位需要换人
        xskill_target_Ulti 3, b, c, d
        EX3=Not EX3
    ElseIf (a = 4 And EX4) Or (a = 8 And Not EX4) Then //4号位需要换人
        xskill_target_Ulti 4, b, c, d
        EX4=Not EX4
    ElseIf (a = 5 And EX1) Or (a = 1 And Not EX1) Then 
        skill_target_Ulti 1, b, c, d
    ElseIf (a = 6 And EX2) Or (a = 2 And Not EX2) Then 
        skill_target_Ulti 2, b, c, d
    ElseIf (a = 7 And EX3) Or (a = 3 And Not EX3) Then
        skill_target_Ulti 3, b, c, d	
    ElseIf (a = 8 And EX4) Or (a = 4 And Not EX4) Then 
        skill_target_Ulti 4, b, c, d	
    End If
End Function

/*------------------------------------------------------------------------------------------*/
/*------------------------------------------------------------------------------------------*/




//重置万能使用技能//注意每场战斗前都要重置
Function resetEX()
    TracePrint "*****************执行resetEX*****************"
    EX1 = False
    EX2 = False
    EX3 = False
    EX4 = False
End Function


//进入战斗前可以用这个来避免敌人上来先制行动，我方无法操作的情况  识别攻击按钮的右端
Function readyToFight()
    TracePrint "**************readyToFight***************"
    dim looptime = 0
    While infight() <> True and looptime < 10
        looptime = looptime + 1
        delay 20
    Wend
    While roundEnd()
        Delay 200
    Wend
End Function


//使用支援者（第一个支援者）
Function helper()
    TracePrint "******************尝试执行helper*******************"
    If inFight() Then 
        TracePrint "使用支援者中"
        FW.SetTextView "即时信息", "使用支援者中", 1400, 0, 520, 30
        click 110, 1020
        click 350, 500
        click 160, 1168
        click 198,722
    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function




//结束回合(持续到新的回合或者战斗结束)
Function roundOver()
    TracePrint "****************尝试执行roundOver*****************"
    If inFight() Then 
        //TracePrint "尝试结束回合"
        FW.SetTextView "即时信息", "尝试结束回合", 1400, 0, 520, 30
        ifNeedRecover
        
        slowClick 122, 1707//点击攻击
        If image.ocrText(100,386,127,446, 0, 1) = "设 置" Then 
            Delay 200
            click 1060,400//点击攻击没生效时，点击空白再点攻击
            Click 122, 1707
        End If

        While roundEnd()  //回合结束时等待
            Delay 200
            click 1060,400//点一下防止卡住
        Wend    
    Else 
        //TracePrint "不在战斗中，无法结束回合！"
    End If
End Function


//结束回合(持续到新的回合或者战斗结束)
Function roundOver_24x7()
    TracePrint "****************尝试执行roundOver*****************"
    If inFight() Then 
        //TracePrint "尝试结束回合"
        FW.SetTextView "即时信息", "尝试结束回合", 1400, 0, 520, 30
        //ifNeedRecover
        
        slowClick 122, 1707//点击攻击
        If image.ocrText(100,386,127,446, 0, 1) = "设 置" Then 
            Delay 200
            click 1060,400//点击攻击没生效时，点击空白再点攻击
            Click 122, 1707
        End If

        While roundEnd()  //回合结束时等待
            Delay 200
            click 1060,400//点一下防止卡住
        Wend    
    Else 
        //TracePrint "不在战斗中，无法结束回合！"
    End If
End Function





//全员蓄力
Function fullbp()
    TracePrint "******************尝试执行fullbp******************"
    If inFight() Then
        TracePrint "全员蓄力"
        fastclick 110, 1300
    Else 
        TracePrint "不在战斗中，无法结蓄力！"
    End If
End Function


//全员交替
Function exchange()
    TracePrint "*****************尝试执行exchange*****************"
    If inFight() Then
        TracePrint "全员交替"
        click 110,1150
    Else 
        TracePrint "不在战斗中，无法全员交替！"
    End If
End Function



//撤退
Function run()
    TracePrint "******************尝试执行run*******************"
    While inFight() //在战斗中点撤离
        click 110, 880
        TracePrint "尝试结束战斗"
    Wend
    TracePrint "结束战斗"
End Function

//追忆之书逃跑
Function run_zhuiyi()
    TracePrint "******************尝试执行run*******************"
    
    While Image.OcrText(335, 700, 370, 740, 0, 1) <> "否"
        click 110, 880
        Delay 200
        TracePrint "逃跑"
    Wend
    click 350,1200//点击 是
    
    While Image.OcrText(455, 917, 491, 993, 0, 1) <> "关闭"
        delay 200
    Wend
    click 460,960//点击 关闭
    While Image.OcrText(815, 50, 850, 115, 0, 1) <> "全部"
        delay 200
    Wend
    TracePrint "结束战斗"
End Function


//战斗结算
Function settlementOver()
    TracePrint "******************尝试执行settlementOver*******************"
    While fightSettlement () //在战斗中或者战斗结算时，点撤离
        click 70, 800
        TracePrint "尝试结束结算"
        FW.SetTextView "即时信息", "尝试结束结算", 1400, 0, 520, 30
    Wend
End Function
  
//长按进入战斗
Function cutScene()
    //Delay 3000
    dim looptime = 0
    While matchPointColor(540, 960, "000000", 1) <> True
        Delay 20
        //TracePrint "等待黑屏"
        FW.SetTextView "即时信息", "等待黑屏", 1400, 0, 520, 30
        looptime = looptime + 1
    Wend
    looptime = 0
    While matchPointColor(540, 960, "000000", 1)
        Delay 20
        //TracePrint "等待退出黑屏"
        FW.SetTextView "即时信息", "等待退出黑屏", 1400, 0, 520, 30
    Wend
    TracePrint "长按屏幕"
    FW.SetTextView "即时信息", "长按屏幕", 1400, 0, 520, 30
    Touch 540, 960, 3000

End Function

//等待文字出现再点击
Function waitAndClick(x1, y1, x2, y2, str, x0, y0)
    dim looptime = 0,lag = 0
    While Image.OcrText(x1, y1, x2, y2, 0, 1) <> str and looptime < 50
        looptime = looptime + 1
        delay 20
    Wend
    If looptime < 500 Then 
        TracePrint "已打开：" & Image.OcrText(x1,y1,x2,y2,0,1)
        Click x0, y0
    Else 
        TracePrint "等待超5秒，已卡死"
        lag = 1
    End If

End Function

/*------------------------------------------------------------------------------------------*/
/*-----------------------------------自定义一键挂机------------------------------------------*/
/*------------------------------------------------------------------------------------------*/



//原地刷怪直到回城镇休息,或游戏崩溃，或循环卡住
Function getExp()
    TracePrint"*********************************************尝试执行getExp**********************************************"
    Dim loopTime=0
    While true //循环直到回城恢复  
        loopTime = loopTime + 1
        TracePrint"循环次数"&loopTime
    	
        If needRecover And inWorld() Then  //需要恢复时
            loopTime=0
            TracePrint "尝试休息"
            If recoverAll() = 1 Then  //假如回到城镇恢复则停止刷怪
                Exit Function
            End If
        End If
	 
        If inFight() Then   //遇到战斗
            loopTime=0
            TracePrint "检测到战斗" 
            chooseFight 
        End If
    	
        If fightSettlement() Then //战斗结算时
            settlementOver 
        End If
            
        If loopTime > 100 or Not inGame() Then //循环超过100次则重启游戏（约30秒）
            loopTime=0
            restartGame 
            Exit Function
        End If
        
        If loopTime > 30 Then //循环超过30次	
            click 1057, 1884 //出现某些界面可以关掉，比如凌晨4点的邮件
        End If   
		
        If 日常(startTime,endTime) = True Then 
            Traceprint "去码头整点薯条!"
            FW.SetTextView "即时信息", "去码头整点薯条", 1400, 0, 520, 30
            日常mark = 1
            Exit Function
        End If
		
        If inWorld() Then //世界中则原地水平移动
            loopTime=0	
            moveY 
        End If
		
        Delay 300
    Wend
End Function

//原地刷怪直到回城镇休息,或游戏崩溃，或循环卡住
Function newgetExp()
    TracePrint"*********************************************尝试执行newgetExp**********************************************"
    Dim loopTime=0
    While true //循环直到回城恢复  
        loopTime = loopTime + 1
        TracePrint"循环次数"&loopTime
    	
        If fightSettlement() Then //战斗结算时
            settlementOver 
        End If
            
        If loopTime > 100 or Not inGame() Then //循环超过100次则重启游戏（约30秒）
            loopTime=0
            restartGame 
            Exit Function
        End If
        
        If loopTime > 30 Then //循环超过30次
            click 1057, 1884 //出现某些界面可以关掉，比如凌晨4点的邮件
        End If   
		
		
        If inWorld() Then //世界中则原地水平移动
            loopTime = 0
            moveZ
            //moveZ
        End If
		
        Delay 300
    Wend
End Function

//原地刷怪直到回城镇休息,或游戏崩溃，或循环卡住
Function 自动战斗()
    TracePrint"*********************************************尝试执行getExp**********************************************"
    Dim loopTime=0
    While true //循环直到回城恢复  
        loopTime = loopTime + 1
        TracePrint"循环次数"&loopTime

        /*If inFight() Then   //遇到战斗
            loopTime=0
            TracePrint "检测到战斗" 
            chooseFight 
        End If*/
    	
        If fightSettlement() Then //战斗结算时
            settlementOver 
        End If

        /*If loopTime > 30 Then //循环超过30次
            click 1057, 1884 //出现某些界面可以关掉，比如凌晨4点的邮件
        End If  */ 
		
		/*If inWorld() = False 
		 cutScene
		End If*/
		
        Delay 300
    Wend
End Function




//叹息冰窟刷怪
Function txbk()
    TracePrint"*********************************************开始执行txbk*********************************************"
    While True
        backWorld 
        openMap
        tpAnywhere 91
        moveMinimapKill 630, 914
        getExp() 
    Wend
End Function



//大树的露珠刷怪
Function dslz()
    TracePrint"*********************************************开始执行dslz**********************************************"
    While True
        backWorld 
        openMap
        tpAnywhere 101
        moveMinimapKill 388,686
        getExp()
    Wend
End Function


//雾明瀑布刷怪
Function wmpb()
    TracePrint"*********************************************开始执行wmpb*********************************************"
    While True
        backWorld 
        openMap
        tpAnywhere 111
        moveMinimapKill 703,829
        getExp()
    Wend
End Function


//针柱之洞刷怪
Function zzzd(n)
    useTeam n
    //tpSleep 1
    TracePrint"*********************************************开始执行zzzd*********************************************"
    While True
        backWorld 
        openMap
        tpAnywhere 121
        moveMinimapKill 242,799
        getExp 
    Wend
End Function

//授富砂宫
Function sfsg(n)
    useTeam n
    TracePrint"**********************************开始执行bsyk*******************************************************"
    While True
        backWorld 
        openMap
        tpAnywhere 132
        moveMinimapKill 640,920
        getExp()
    Wend
End Function

//久远的流沙
Function jyls(n)
    useTeam n
    TracePrint"***************************************开始执行bsyk******************************************"
    While True
        backWorld 
        openMap
        tpAnywhere 132
        Swipe 570, 454, 400, 454
        delay 2000
        backWorld
        moveMinimapKill 640,920
        getExp()
    Wend
End Function

Function zjh(n)
    useTeam n
    TracePrint"*********************************************************************************************开始执行zjh*********************************************************************************************"
    While True	
        backWorld 
        openMap
        tpAnywhere 41
        moveMinimapKill 671, 815
        Swipe 570, 454, 400, 454
        Delay 5000
        moveMinimapKill 583, 635
        Swipe 570, 454, 400, 454
        Delay 5000
        moveMinimapKill 432, 572
        Swipe 600, 1241, 522, 661
        Delay 2000
        Swipe 600,1241, 522,661
        Delay 7000
        moveMinimapKill 727, 586
        getExp()
    Wend
End Function

Function rtqk(n)
    useTeam n
    TracePrint"***************************************开始执行bsyk******************************************"
    While True
        backWorld 
        openMap
        tpAnywhere 160
        backWorld
        moveMinimapKill 511,820
        newgetExp()
    Wend
End Function





/*------------------------------------------------------------------------------------------*/
/*-----------------------------------------追忆之书------------------------------------------*/
/*------------------------------------------------------------------------------------------*/

Function 追忆之书(option1, option2, option3, times)
    dim l = 1,lag = 0
    Rem start0

    backWorld 
    Click 175,1108 //点救世的手抄本
    delay 1500
    waitAndClick(1000, 210, 1060,490, "救世的手抄本", 650,450)//点大陆的追忆
    waitAndClick(1010, 445, 1060, 665, "大陆的记录", 955, 1460)//点筛选
    click 100,720//重置
    click 640,400//战斗事件
    click 100,1200//确定
    click 830,100//点击全部
    delay 500
    waitAndClick(815, 80, 847,152, "全部",830 - option1 * 130, 100)//选择option1，无推荐栏时候用
    //waitAndClick(815, 80, 847,152, "全部",700 - option1 * 130, 100)//选择option1，有推荐栏时候用
    delay 500
    waitAndClick(810, 90, 850, 150,"全部",830 - option2 * 130, 100)//选择option2，无推荐栏时候用
    //waitAndClick(810, 90, 850, 150,"全部",7000 - option2 * 130, 100)//选择option2，有推荐栏时候用
    If image.OcrText(815,50,850,115,0,1) <> "全部" Then 
        click 830 - option2 * 130, 100//没点击到时再点一下选择option2，无推荐栏时候用
        //click 7000 - option2 * 130, 100//没点击到时再点一下选择option2，有推荐栏时候用
    End If
	
    Rem startFight
    Delay 500
    waitAndClick(815, 55, 850,115, "全部", 1160 - option3 * 360, 1600)//选择option3
    Delay 500
    If matchPointColor(440, 1575, "715925", 5) Then 
        click 1160 - option3 * 360, 1600//没点击到时再点一下阅读
    End If
    traceprint "选择" & option3
    While Image.OcrText(145, 700, 185, 740, 0, 1) <> "否"
        delay 20
    Wend
    click 165,1200//点击 是
    TracePrint "开始第" & l & "次战斗"
    FW.SetTextView "即时信息", "开始第" & l & "次战斗", 1400, 0, 520, 30
    cutScene//过场动画

    
 /*---------------------------------------选择自定义战斗---------------------------------------*/

    fight追忆(option3)

 /*-------------------------------------------------------------------------------------------*/
    TracePrint "战斗完成"
    TracePrint "第" & l & "次战斗结束"
    FW.SetTextView "即时信息", "第" & l & "次战斗结束", 1400, 0, 520, 30
    If Not inGame() or lag = 1 Then 
        TracePrint "重启"
        Goto start0
    End If
    
    TracePrint"运行" & Round(TickCount() /60000,1) & "分钟," & "总战斗" & l & "次"
    FW.SetTextView ("主窗口", "运行 " & Round(TickCount() /60000,1) & " 分钟," & "总战斗 " & l & " 次", 0, 0, 1400, 30)
    l = l + 1
    
    If l < times Then 
        Goto startFight
    End If
    
End Function

Function 冒险家(n)
    useTeam n

    backWorld 
    slowclick 150,330 //队伍
    Delay 500
    slowclick 1040,530 //旅团组合
    Delay 500
    slowclick 840,200 //组合1
    Delay 500
    slowclick 165,250 //导出组合
    Delay 500
    slowclick 355,1200//是
    backWorld 

    tpSleep 1
    backWorld 
    openMap 
    tpAnywhere (999)//目的地999追忆之塔

    moveMinimap 625, 740
    Swipe 600,1241, 522,661
    delay 5000
    Swipe 600,1241, 522,661
    Delay 500
    Swipe 600,1241, 522,661
    delay 5000
    moveMinimap 366, 905

    click 634 , 1167
    Delay 500
    click 374 , 666//去3层
    Delay 8000

    moveMinimapRun 770, 1350

    click 540 , 1187 //点对话
    Delay 500
    click 130 , 1770 //点打探
    Delay 2000
    click 660 , 1450 //点赢取
    Delay 500
    click 230 , 1160 //点赢取
    Delay 500
    click 310 , 1200 //确定
    Delay 500
    click 310 , 1200 //确定
    Delay 500
    click 310 , 1200 //确定

    Dim loopTime = 0
    While inFight() = False and looptime < 20
        Delay 200
        loopTime = loopTime + 1
    Wend

    If inFight() Then   //遇到战斗
        delay 200
        TracePrint "检测到战斗"  
        readyToFight 
/*回合1
Sskill 1, 2, 0
Sskill 2, 1, 0
Sskill 3, 1, 0
Sskill 4, 3, 0
fullbp
roundOver_24x7
//回合2
Sskill 4, 2, 0
fullbp 
roundOver_24x7
//回合3
Sskill 1, 5, 0
Sskill 2, 5, 0
Sskill 3, 5, 0
Sskill 8, 3, 3
roundOver_24x7*/
        Click 114, 737
        roundOver_24x7
    End If 

    backWorld 
    slowclick 150,330 //队伍
    Delay 500
    slowclick 1040,530 //旅团组合
    Delay 500
    slowclick 755,200 //组合2
    Delay 500
    slowclick 165,250 //导出组合
    Delay 500
    slowclick 355,1200//是

End Function

Function 刚魔石1(n)

    useTeam n
    tpSleep 1
    backWorld 
    openMap 
    tpAnywhere (999)//目的地999追忆之塔

    moveMinimap 625, 740
    Swipe 600,1241, 522,661
    delay 5000
    Swipe 600,1241, 522,661
    Delay 500
    Swipe 600,1241, 522,661
    delay 5000
    moveMinimap 366, 905

    click 634 , 1167
    Delay 500
    click 374 , 666//去3层
    Delay 8000

    moveMinimapKill 742,803
    Swipe 300,300, 500,300
    Delay 8000
    moveMinimapKill 340,1238
    Swipe 300,300, 300,500//右滑
    Delay 8000
    moveMinimapKill 177,822
    Swipe 300,500, 300,300//左滑进入战斗

    Dim loopTime = 0
    While inFight() = False and looptime < 20
        Delay 200
        loopTime = loopTime + 1
    Wend
    If inFight() Then   //遇到战斗 普攻打怪
        delay 200
        TracePrint "检测到战斗"  
        readyToFight 
        Click 114, 737
        roundOver_24x7
    End If 

End Function

Function 刚魔石2(n)

    useTeam n
    tpSleep 1
    backWorld 
    openMap 
    tpAnywhere (999)//目的地999追忆之塔

    moveMinimap 625, 740
    Swipe 600,1241, 522,661
    delay 5000
    Swipe 600,1241, 522,661
    Delay 500
    Swipe 600,1241, 522,661
    delay 5000
    moveMinimap 366, 905

    click 634 , 1167
    Delay 500
    click 374 , 666//去3层
    Delay 8000

    moveMinimapKill 218,491
    Swipe 300,500, 300,300
    Delay 8000
    moveMinimapKill 753,479
    drag 300,300, 500,300//上滑进入战斗

    Dim loopTime = 0
    While inFight() = False and looptime < 20
        Delay 200
        loopTime = loopTime + 1
    Wend
    If inFight() Then   //遇到战斗 普攻打怪
        delay 200
        TracePrint "检测到战斗"  
        readyToFight 
        Click 114, 737
        roundOver_24x7
    End If 

End Function



Function 牛(n)

    useTeam n

    backWorld
    openMap
    tpAnywhere (999)//目的地999追忆之塔

    moveMinimap 625, 740
    Swipe 600,1241, 522,661
    delay 5000
    Swipe 600,1241, 522,661
    Delay 500
    Swipe 600,1241, 522,661
    delay 5000
    moveMinimap 366, 905

    click 634 , 1167
    Delay 500
    click 540 , 1250//去2层
    Delay 8000

    moveMinimapKill 230, 890
    Swipe 600,1241, 522,661
    Delay 8000
    moveMinimapKill 485, 432
    Swipe 570,454, 548,858
    Delay 8000
    moveMinimapKill 769, 1306

    drag 300,300, 500,300//上滑进入战斗

    Dim loopTime = 0
    While inFight() = False and looptime < 20
        Delay 200
        loopTime = loopTime + 1
    Wend


    If inFight() Then   //遇到战斗 普攻打死牛
        delay 200
        TracePrint "检测到战斗"  
        readyToFight 

        Click 114, 737
        roundOver_24x7
   
    End If 

End Function

Function 看广告()

    rem start0
    backWorld 
    click 190, 130
    delay 1000
    click 190, 585
    delay 2000
    If not MatchPic1(260, 134, 291, 285, "adv", 1) Then 
        goto start0
    End If
	
    rem start1
    clickPic(260, 134, 291, 285, "adv", 1)
    clickPic(90,1080,135,1135, "playadv", 1)
    clickPic 326, 915, 377, 1003, "confirmadv", 1
    If not matchpic1(971, 1697, 1022, 1783, "countdownadv", 1) Then 
        clickPic(960,1754,1036,1920,"closeadv", 1)	
    End If
    clickPic(403,912,453,1004, "confirmadv", 1)
    clickPic(430,1037,494,1233, "continueadv", 1)
    If matchPointColor(242, 176, "737475", 1) and matchPointColor(295, 285, "161D1E", 1) Then 
        traceprint "广告已看完！"
        Exit Function
    Else 
        goto start1
    End If
	
End Function

Function 追忆碎片()
    backWorld

    click 874, 1618//打开小地图
    delay 300
    If Image.OcrText(950, 150, 1010, 350, 0, 1) <> "无名 小镇" Then 
        TracePrint Image.OcrText(950, 150, 1010, 350, 0, 1) & ",不在无名小镇"
        backWorld
        openMap
        tpTown 0
        TracePrint "传送到无名小镇"
        FW.SetTextView "即时信息", "传送到无名小镇", 1400, 0, 520, 30
    Else 
        backWorld
    End If 

    moveMinimap 376, 1013
    TracePrint "移动到路口"
    delay 500
    Swipe 746, 960, 446, 960
    TracePrint "下滑"
    delay 500
    moveMinimap 549,1090
    delay 500
    Swipe 446,660, 746,660
    delay 5000
    If inWorld() Then 
        click 393,522//点击小人
    End If
    While (Not matchPointColor(160, 1720, "3B7878", 1) And Not matchPointColor(160, 1840, "3B7878", 1))//等待右下角打探图标出现
        Delay 500
        TracePrint "-----------等待右下角打探出现-----------"
    Wend
    Click 135,1785 //点击打探
    While (Not matchPointColor(658,1400, "60ACCA", 1) And Not matchPointColor(890,340, "FFFFFF", 1))//等待购买图标出现
        Delay 500
        TracePrint "-----------等待购买图标出现-----------"
    Wend
    Click 661,1392//点击购买
    For 3
        While (Not matchPointColor(266,945, "A5987A", 1) And Not matchPointColor(229,1014, "77612F", 1))//等待购买物品出现
            Delay 500
            TracePrint "-----------等待购买物品出现-----------"
        Wend   
        click 266,945//还价
        TracePrint "-----------还价-----------"
        Delay 500
        click 282,1195//确定
        TracePrint "-----------确定-----------"
    Next
    backWorld
End Function

Function 红龙(n)
    useTeam n
    tpSleep 1
    backWorld
    openMap
    tpAnywhere (999)//目的地999追忆之塔

    moveMinimap 705, 874//走到追忆之塔入口火苗
    TracePrint"走到追忆之塔入口火苗"
    FW.SetTextView "即时信息", "走到追忆之塔入口火苗", 1400, 0, 520, 30
    slowClick 650, 960 //点击上方火苗
    slowClick 375, 670 //点击战争的篝火2
    TracePrint "进入战争的篝火"
    FW.SetTextView "即时信息", "进入战争的篝火2", 1400, 0, 520, 30
    While inWorld() <> True
        click 1057, 1884
        delay 200
        TracePrint "点击并等待回到主界面"
        FW.SetTextView "即时信息", "点击并等待回到主界面", 1400, 0, 520, 30
    Wend
    slowClick 787, 960//点击红龙老窝
    Delay 2000
    slowClick 453,1247//是
    moveMinimap 811,797
    drag 461,1099, 461,899

    Dim loopTime = 0
    While inFight() = False and looptime < 20
        Delay 200
        loopTime = loopTime + 1
    Wend

    If inFight() Then   //遇到战斗
        delay 200
        TracePrint "检测到战斗"  
        readyToFight 
        //回合1	
        Sskill 1, 3, 0
        Sskill 6, 3, 3
        Sskill 3, 1, 3
        Sskill 4, 1, 0
        roundOver_24x7
        //回合2
        Sskill 1, 2, 0
        Sskill 2, 2, 1
        Sskill 7, 1, 1
        roundOver_24x7
        //回合3
        Sskill 1, 1, 2
        Sskill 2, 1, 3
        Sskill 7, 1, 3
        Sskill 4, 1, 2
        roundOver_24x7
        //回合4
        Sskill 2, 5, 0
        Sskill 7, 5, 0
        fullbp
        roundOver_24x7
/*回合1	
Sskill 1, 3, 0
Sskill 6, 3, 3
Sskill 3, 1, 3
Sskill 4, 3, 0
roundOver_24x7
//回合2
Sskill 1, 2, 0
Sskill 2, 2, 2
Sskill 7, 1, 2
Sskill 4, 2, 3
roundOver_24x7
//回合3
Sskill 2, 1, 0
Sskill 3, 1, 1
roundOver_24x7
//回合4
Sskill 1, 1, 2
Sskill 2, 1, 3
Sskill 7, 1, 3
Sskill 4, 1, 2
roundOver_24x7 
//5回合
Sskill 2, 5, 0
Sskill 7, 5, 0
fullbp
roundOver_24x7 
   While inFight()
     fullbp
     roundOver_24x7
    Wend*/
    End If
End Function

Function 一点小心意(n)
    backWorld
    useTeam n
    backWorld
    openMap
    tpAnywhere (21)//雪林闲地
    moveMinimap 900, 892
    Delay 500
    slowClick 625,957 //点击光圈
    slowClick 450,1270 //点击是
    Delay 8000
    moveMinimapKill 540, 675
    Delay 500
    slowClick 610,960 //点击光圈
    Delay 8000
    moveMinimapKill 585, 765
    Delay 500
    If inWorld() Then 
        click 565,1252//点击小人
    End If
    While (Not matchPointColor(160, 1720, "61412D", 1) And Not matchPointColor(160, 1840, "61412D", 1))//等待右下角打探图标出现
        Delay 500
        TracePrint "-----------等待右下角打探出现-----------"
    Wend
    Click 135,1785 //点击打探
    While (Not matchPointColor(661,1385, "D28E6F", 1) And Not matchPointColor(890,340, "FFFFFF", 1))//等待请求图标出现
        Delay 500
        TracePrint "-----------等待请求图标出现-----------"
    Wend
    Click 661,1385//点击请求
    While (Not matchPointColor(230,683, "4E4E4E", 1) And Not matchPointColor(231,833, "515151", 1))//等待请求物品出现
        Delay 500
        TracePrint "-----------等待请求物品出现-----------"
    Wend
    click 230,1172//请求
    TracePrint "-----------请求-----------"
    click 300, 1200//确定
    TracePrint "-----------确定-----------"
    Delay 1000
    click 320, 960//跳过对话
    backWorld
End Function


//搜索图片
Function MatchPic1(x1, y1, x2, y2, Pic, dirc)
    Dim intX, intY
    FindPic x1,y1,x2,y2,"Attachment:" & Pic & ".png","000000",dirc,0.75,intX,intY
    If intX > -1 Then
        //TracePrint intX & "," & intY
        MatchPic1 = True
    Else 
        MatchPic1 = False
    End If
End Function

//开关委托换位
Function 开关自动交替
    backWorld 
    click 162,130//点击菜单
    Delay 500
    click 155,1735//点击其他
    Delay 500
    click 719,940//点击战斗设定
    click 698,345//点击委托战斗
    click 874,1622//开关交替
    click 137,1274//点击确定
    backWorld 
End Function




/*------------------------------------------------------------------------------------------*/
/*-----------------------------------v1.1.0更新日志------------------------------------------*/
/*------------------------------------------------------------------------------------------*/

//1.删除遇猫提示功能
//2.更新新地图刷怪功能*
//3.更新100%抓猫（需支援者）*
//4.增加一些新的注意事项
//5.增加游戏崩溃重启游戏功能*
//6.脚本稳定性增强

/*------------------------------------------------------------------------------------------*/
/*-----------------------------------v1.1.1更新日志------------------------------------------*/
/*------------------------------------------------------------------------------------------*/

//1.重启游戏功能优化
//2.释放技能延时增长，释放更稳定
//3.优化状态判定
//4.增加了新地图雾明瀑布的刷怪功能*
//5.区分55级猫和50级猫，现在可以选择用哪种方式对付哪种敌人*
//6.现在会记录遇到敌人的次数*
//7.优化click函数，点击更稳定
//8.优化战斗相关函数，现在判定战斗中更准确
//9.更改脚本排版
//10.增加Sskill函数,更加符合直觉的释放技能


/*------------------------------------------------------------------------------------------*/
/*-----------------------------------v1.1.2更新日志------------------------------------------*/
/*------------------------------------------------------------------------------------------*/

//1.增加“稳定杀50双猫”和“洁哥一打一跑”的新战斗流程
//2.增加新的地图自动刷怪功能
//3.延长左右移动刷怪延迟
//4.优化roll操作
//5.简化脚本日志
//6.将状态判断并入到roundover中，提供修改需要恢复条件的功能

/*------------------------------------------------------------------------------------------*/
/*-----------------------------------my更新日志------------------------------------------*/
/*------------------------------------------------------------------------------------------*/


//0. 抓猫自定义
//1. 增加fastclick快速点击功能，延迟200ms，用于战斗结算
//2. 战斗结算点击位置改到攻击按键右端，坐标100, 1840
//3. 遇猫记录追加脚本运行计时
//4. 低HPSP时描述语句追加对应人物位置
//5. 篝火自动功能，改动有点多，懒得写了
//1.1.6 增加了沙漠2地图
//6. infight增加了必杀识别，和黑屏等待
//1.1.8 完善功能，历战通行证恢复、单刷历战、自动技能支持释放必杀、skill_boss选中boss作为施法对象
//1.1.9 篝火回城睡觉后从离开的地图继续，而不是从头再跑。改善和修复选择队伍功能；篝火1可以选择队伍；优化历战告别功能
//修复bug: 由于targetMap = 6写错了位置，导致其实篝火还是从头跑; 雪2地图序号其实应该是10，写的2导致不战斗不逃跑
//修复bug: 雪2的地图序号暂时用10，脚本里写的2导致卡住
//
//1.2.0 增加必杀释放状态判断，放必杀时角色卡片不是黑底色，不读取sp
//完成spPercent,以10%为步长来判断sp剩余。似乎原来的更适用？可以设置两人缺蓝就恢复 
//放必杀后必杀条灰色加入判断
//换人后，使用roll 3bp 实际只有1bp,结果是使用0bp。尝试延长roll delay来改善
//recover加上backworld
//篝火战斗结束后等待world改为backWorld
//1.2.1 增加收菜功能
//增加篝火2 海 4个磨石怪
//收菜功能优化
//restartGame增加了循环判断，防止卡死在黑屏界面
//1.2.2
//删掉了崖2boss
//修改了海2的调用方法，不用该camfire2了
//1.2.3
//a) 功能新增：
//新增skill_target,可以选中施法对象,目前支持三个斗技场对象（要带上引号） "缇奇莲" "缇奇莲上" "缇奇莲下" "戈洛萨姆" "瓦尔坎" ……与 己方8个位置：数字 1-8 ，还有默认后排boss 0
//b) 优化：
//修改小地图移动目的地到小地图水平路线上，避免怪物脚底下黑路导致卡住。（新增了drag函数，拖动1秒）//崖2的竖路比较长，还是需要走一小段给踩亮
//重启游戏 检测到开始画面时，多等待两秒+点击一次
//增加延迟，等待浮窗消失 避免浮窗遮挡队伍黄点导致切换队伍失败
//延长小地图找怪的delay，避免小地图打开太慢导致的跳怪
//去掉skill xskill的自动放必杀技功能
//抓一圈历战支援时直接提前全告别。否则：如果第＞1个历战在支援列表，会把前面的都给告别了
//1.2.4
//功能新增：
//追忆之书
//篝火2新的磨石怪（和雪原猫）
//功能优化：
//篝火2地图已经连起来了所以从 6 沙漠开始跑一圈
//缩短了一些操作延迟，可能会导致操作失败（目前尚未遇到x 群友遇到roll太快甩飞地图问题，delay再加到100）
//exkill换位后delay100
//backworld升级，增加了追忆之书战斗中逃跑点击是
//hp检测增加了一秒延迟，避免后排挂件的buff遮挡血条
//增加了backworld10次重启
//减少hpsp检测的print
//1.2.4+
//追忆之书阅读没点到时追点一下
//roundover增加空白处点击，防止卡在点击攻击前
//fulldp更名为fullbp
//追忆之书选择option的文本识别区域坐标调整
//1.2.5
//简化了fight追忆()的用法
//增加了倒地逃跑功能
//修复了花田bug，789级也可以用了
//1.2.6
//双猫 判断两只袋子颜色 B1E2E2
//55猫写了两个相似的颜色
//去掉了55猫本体颜色识别
//getExp的showmessage移动
//取消ifNeedRecover的delay。后排有挂件时可能遮挡，待解决。
//抓猫刷野第一次释放技能前delay100，不确定是否能防止卡技能
//增加了截图功能和定时执行功能，分别在choosefight和日常里
//TouchMove的滑动时间延长到200
//click delay 改回500
//增加永久浮窗FW.SetTextView，去掉临时浮窗ShowMessage
//
//
//增加了补选技能功能，技能没选上时循环选择
//确认传送操作 前面delay增加到800
//
//ifNeedRecover修改，去掉了加法运算。还需要再提速。
//roundover中，ifNeedRecover移动到点击攻击前
//新增roundOver_24x7，不检测hpsp,用于刷野抓猫
//牧羊岩历战NPC坐标调整
//打开队伍操作优化
//篝火2增加了68地图开放的怪，包括林2 沙2boss