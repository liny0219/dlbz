//交流群群号213459239
//分辨率1920x1080 DPI 270-320 推荐320 
//游戏内 原画，60帧，1080p，视野标准，超分辨率算法开启

Dim ambiguity =0.98
Dim app,FM=Array(),loop1=0,loop2=0,markTime,double=0
//三水家mod
Dim checkRN = 0
Dim checkBoss = 0

startGame()//兼容B服和网易服，直接运行脚本可以打开游戏


FW.NewFWindow("浮窗", 0, 1050, 1920, 30)
//创建文字控件
FW.Show ("浮窗")
FW.AddTextView "浮窗", "主窗口", "", 0, 0, 1400, 30
FW.AddTextView "浮窗", "即时信息", "脚本运行中", 1400, 0, 520, 30
FW.Opacity "浮窗", 0
FW.SetTextColor("主窗口","FFFFFF")
FW.SetTextColor("即时信息","FFFFFF")
FW.SetTextView "即时信息", "", 1400, 0, 520, 30

Select Case ReadUIConfig("地区")
    Case 0
        FM(0)={{158,520},{158,565},{146,719},{264,796},{412,887},{695,729},{690,1014},{593,1015},{592,1244},{324,1248},{326,1070},{146,1132},{148,897}}
		FM(1)={{594,677},{632,970},{602,1050},{551,775},{600,1107},{592,976},{533,1107},{563,797},{605,960},{606,1318},{599,958},{583,930},{561,1170}}
End Select
Thread.Start(确定)
Sub 确定()
	While true
	clickPic 50, 491, 812, 1446, "确定", 1
	clickPic 330,890,739,1377, "重试", 1
	Delay 1000
	loop1 = Thread.GetShareVar("loop1")
	loop2 = Thread.GetShareVar("loop2")
	markTime = Thread.GetShareVar("markTime")

	FW.SetTextView ("主窗口", "运行" & Round(TickCount()/ 60000, 1) & "分钟，已完成" & loop1 & "次，失败" & loop2 &"次，本次计时：" & Round((TickCount() - markTime) / 60000, 1) & "分钟，场均" & Round(markTime / 60000 / loop1, 1) & "分钟。" , 0, 0, 1000, 30)
	Wend
End Sub



逢魔 ReadUIConfig("难度"),ReadUIConfig("地区")

function 逢魔(难度,地区)
    dim lp = 0
    
    
    Rem start0
    backWorld 
    
    //判断是否在逢魔地图，是则返回城镇
    If not matchPointColor(181, 521, "CBCCCC", 1) Then 
    	TracePrint "在逢魔地图"
    	backTown(地区)
    End If

    
    
    
    
    town(地区)//传送到对应地区的城镇中
	
    moveMinimap FM(0,0,0),FM(0,0,1) //移动逢魔入口
    TracePrint"进入逢魔"
    FW.SetTextView ("即时信息", "开始逢魔", 1500, 0, 420, 30)
   
    Rem start1  

    click FM(1,0,0),FM(1,0,1)
    Delay 1000
    
    
    
	markTime = TickCount()
	Thread.SetShareVar "loop1",loop1
	Thread.SetShareVar "loop2",loop2
	Thread.SetShareVar "markTime",markTime  
    FW.SetTextView ("主窗口", "运行" & Round(markTime / 60000, 1) & "分钟，已完成" & loop1 & "次，失败" & loop2 &"次，本次计时：" & Round((TickCount() - markTime) / 60000, 1) & "分钟，场均" & Round(markTime / 60000 / loop1, 1) & "分钟。" , 0, 0, 1000, 30)
    
   //判断是否在选难度界面 
    lp=0
    while (not matchPointColor(348,1274, "715A25",1) or not matchPointColor(361,1116, "745F2E",1)) and lp < 20       
        lp = lp + 1
        Delay 100
        TracePrint"不在选难度界面"
    Wend
    If lp = 20 Then 
        goto start0
    End If

    
    lp = 0
    //降低难度为 1
    While not matchPointColor(554,836, "717475", 1)and lp < 20
        fastclick 539,838
        lp = lp + 1
    Wend
        
    //选择难度    
    if 难度+0>0 then
        for t = 1 to 难度
            fastclick 541,1089
        Next
    End If
    
  	//进入逢魔地图
  	lp=0
  	click 355,1081
    While MatchPic(169, 911, 561, 1450, "start", 1)
    	click 355, 1081
    	lp=lp+1
    	If lp = 20 Then 
    		goto start0
    	End If
    	TracePrint "未进入地图"
    Wend
    
    traceprint "开始"
    FW.SetTextView ("即时信息", "开始", 1500, 0, 420, 30)
    Delay 2000
    FW.SetTextView ("即时信息", "进入地图", 1500, 0, 420, 30)
    
     地图探索(地区)
    loop1 = loop1 + 1

    If ReadUIConfig("（SP检测）恢复") or ReadUIConfig("打完一次恢复") Then  
    	If recoverAll() = 1 Then 
    		Goto start0
    	End If
    End If
    
    
    Goto start1 
End Function


Function 地图探索(地区)

    dim A=Array(),b=0,m=0,k,n=0,c=0
    
    //一阶段
    TracePrint "一阶段"
    For j = 1 To 12
    	Rem start0
    	
       // FW.SetTextView ("主窗口", "运行" & Round(TickCount()/ 60000, 1) & "分钟，已完成" & loop1 & "次，失败" & loop2 &"次，本次计时：" & Round((TickCount() - markTime) / 60000, 1) & "分钟，场均" & Round(markTime/ 60000 / loop1, 1) & "分钟。" , 0, 0, 1000, 30)
        //移动到探索点
        moveMinimap FM(0, j, 0), FM(0, j, 1)
        
        If matchPointColor(874,1618, "9E66BD", 30) or matchPointColor(874,1618, "9965BA", 30)  Then 
        	TracePrint "检测到探索点已显形"
        	Exit For
        End If
        
        //点击探索点
        slowClick FM(1,j, 0), FM(1,j, 1)
        Delay 1000
		//小boss战斗
        If inFight() Then 
            FW.SetTextView ("即时信息", "战斗中", 1500, 0, 420, 30)
            
            If ReadUIConfig("小怪战斗")=0 or 精英怪() Then
            
            Select Case ReadUIConfig("精英怪战斗")
            	Case 0
            		autokill 
            	Case 1
            		战斗配置1 
            	Case 2
            		战斗配置2
            End Select
            
            //五回合未结束，放弃战斗
            If inFight() Then 
            	TracePrint "五回合未结束，放弃战斗"
                click 93, 887
                While  inGame() and inFight()
                Delay 1000
                	click 93, 887
                Wend
                click 355,1081
                While inGame() and not inWorld()
                Delay 1000
                	click 355,1081
                Wend
                loop2 = loop2 + 1
                Exit Function
            End If
            
            FW.SetTextView "即时信息", "战斗结束", 1500, 0, 420, 30
            b=1
            Goto start0
            Else 
            	TracePrint"野怪委托战斗"
            	If double = 0 Then 
            	autokill 
            	 double = 1
            	 Else 
            	 readyToFight
            	 roundOver 
            	 End If
            	
            	Goto start0
            End If
        End If
		
        If b = 0 and j = 12 and m<5 Then        	
        	TracePrint "检测到精英怪未击杀"
        	m=m+1
            Goto start0
        ElseIf m > 4 Then
        	TracePrint "进入某种循环，返回城镇"
			backTown (地区)
        	loop2 = loop2 + 1
        	Exit Function
        End If
    Next
    
    //二阶段
    TracePrint "探索点已显形，进入二阶段"
    slowClick 930, 1618
    m=0
    While inGame () and inWorld()
    	slowclick 930, 1618
    	TracePrint "打不开小地图"
    	m = m + 1
    	If m = 20 and not matchPointColor(181, 521, "CBCCCC", 1) Then 
    		backTown (地区)
    		loop2 = loop2 + 1
    		Exit Function
  		End If
    	
    Wend
    
    For i = 1 To 12
   			If matchPointColor(FM(0,i, 0), FM(0,i, 1), "9E66BD", 50) or matchPointColor(FM(0,i, 0), FM(0,i, 1), "9965BA", 50)  Then 
   				TracePrint "已知探索地： " & i
   				A(c) = i
   				c = c + 1
   			End If
   		Next
   		
   		backWorld
   		m = 0
   		
    	For i = 0 To UBOUND(A)
    	
    	Rem start1
    	
   		moveMinimap FM(0, A(i), 0), FM(0, A(i), 1)
   		
   		slowClick FM(1,A(i), 0), FM(1,A(i), 1)
        Delay 1000
		//小boss战斗
        If inFight() Then 
            FW.SetTextView "即时信息", "战斗中", 1500, 0, 420, 30
            
            If ReadUIConfig("小怪战斗")=0 or 精英怪() Then
            Select Case ReadUIConfig("精英怪战斗")
            	Case 0
            		autokill 
            	Case 1
            		战斗配置1 
            	Case 2
            		战斗配置2
            End Select
            
            //五回合未结束，放弃战斗
            If inFight() Then 
            	TracePrint "五回合未结束，放弃战斗"
                click 93, 887
                While  inGame() and inFight()
                Delay 1000
                	click 93, 887
                Wend
                click 355,1081
                While inGame() and not inWorld()
                Delay 1000
                	click 355,1081
                Wend
                loop2 = loop2 + 1
                Exit Function
            End If
            
            FW.SetTextView "即时信息", "战斗结束", 1500, 0, 420, 30
            b=1
            Goto start1
            Else 
            	TracePrint"野怪委托战斗"
            	If double = 0 Then 
            	autokill 
            	 double = 1
            	 Else 
            	 readyToFight
            	 roundOver 
            	 End If
            	 Goto start1
            End If
        End If
		
        If b = 0 and i = UBOUND(A) and m<5 Then        	
        	TracePrint "检测到精英怪未击杀"
        	m=m+1
            Goto start1
        ElseIf m > 4 Then
        	TracePrint "进入某种循环，返回城镇"
			backTown (地区)
        	loop2 = loop2 + 1
        	Exit Function
        End If
    Next
   	
   	//三阶段
   	TracePrint "三阶段，BOSS阶段"
    Rem start2
    
   // FW.SetTextView ("主窗口", "运行" & Round(TickCount()/ 60000, 1) & "分钟，已完成" & loop1 & "次，失败" & loop2 &"次，本次计时：" & Round((TickCount() - markTime) / 60000, 1) & "分钟，场均" & Round(markTime / 60000 / loop1, 1) & "分钟。" , 0, 0, 1000, 30)
    m=0
    While inGame() and not inWorld()
        click 352, 823
        click 428, 959
        Delay 1000
        TracePrint "返回世界中"
        m = m + 1
        If m = 20 Then 
        	restartGame 
        	If not matchPointColor(181, 521, "CBCCCC", 1) Then 
    		backTown(地区)
    		End If
    		loop2 = loop2 + 1
    		Exit Function
        End If
    Wend
    
    click 930, 1618
    
    k=0
    For j = 1 To 12
        k=j
        If matchPointColor(FM(0,j, 0), FM(0,j, 1), "9E66BD", 50) or matchPointColor(FM(0,j, 0), FM(0,j, 1), "9965BA", 50) Then 
            Exit For
        End If	
    Next 
     
    backWorld 
    Rem start3
    moveMinimap FM(0,k, 0), FM(0,k, 1)
    slowClick FM(1,k, 0), FM(1,k, 1)
    m = 0
    While inGame() and not inFight()
    	TracePrint "三阶段，未检测到战斗"
        
        If n > 3 Then 
        	TracePrint "返回城镇"
        	backTown (地区)
        	loop2 = loop2 + 1
        	Exit Function
        End If
        If m > 15 Then 
        	TracePrint "三阶段，未检测到战斗"
        	n=n+1
            goto start2
        End If
		click 356, 1197
        m = m + 1
    Wend
    
  //  FW.SetTextView ("主窗口", "运行" & Round(TickCount()/ 60000, 1) & "分钟，已完成" & loop1 & "次，失败" & loop2 &"次，本次计时：" & Round((TickCount() - markTime) / 60000, 1) & "分钟，场均" & Round(markTime / 60000 / loop1, 1) & "分钟。" , 0, 0, 1000, 30)
    If inFight() Then 
		
        If ReadUIConfig("小怪战斗")=0 or BOSS() Then
        FW.SetTextView ("即时信息", "战斗中", 1500, 0, 420, 30)
        Select Case ReadUIConfig("BOSS战斗")
            	Case 0
            		autokill 
            	Case 1
            		战斗配置1 
            	Case 2
            		战斗配置2
            End Select
        If inFight() Then 
        	TracePrint "战斗还未结束，重启游戏"
            restartGame 
            n=n+1
            goto start3
        End If
        FW.SetTextView "即时信息", "战斗结束", 1500, 0, 420, 30
        Else 
            TracePrint"野怪委托战斗"
            	If double = 0 Then 
            	autokill 
            	 double = 1
            	 Else 
            	 readyToFight
            	 roundOver 
            	 End If
            	 goto start3
            End If
    End If
    m=0
    While inGame() and not inWorld()
        click 161, 1031
        Delay 1000
        TracePrint "正在返回世界中"
        m = m + 1
        If m = 20 Then 
        	restartGame  
        	If not matchPointColor(181, 521, "CBCCCC", 1) Then 
    		backTown(地区)
    		End If
    		loop2 = loop2 + 1
    		Exit Function
        End If
    Wend
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
        click 353,823
        TracePrint "------------------------------------点击右上角关闭窗口"
        Delay 200
        loopTime = loopTime + 1
        TracePrint"循环次数"&loopTime
        If loopTime > 30 Then //循环超过30次
            TracePrint "-----------------------------------------------------------请debug"
            FW.SetTextView "即时信息", "循环超过50次，请debug", 1400, 0, 520, 30
            restartGame 	
        End If
        If inFight() Then 
            Exit Function
        End If
    Wend
    loopTime=0
    While inGame() And Not whereMinimap(x, y)
        Delay 1000
         loopTime = loopTime + 1
         If loopTime > 30 Then //循环超过30次 
            restartGame 	
        End If
        If inFight() Then 
            Exit Function
        End If
    Wend
    TracePrint "已经移动至指定位置"
    FW.SetTextView ("即时信息", "到达目的地", 1400, 0, 520, 30)
End Function

//暂停战斗
Function stopFight()
    TracePrint"******************尝试执行stopFight*******************"
    FW.SetTextView ("即时信息", "尝试执行stopFight", 1400, 0, 520, 30)
    While inFight()
        Delay 1000
    Wend
End Function

//大霸，启动!
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
        While not inWorld() and looptime < 80
            
   
            click 300, 850
            Delay 500
            click 500, 850
            
            looptime = looptime + 1
            traceprint looptime
        Wend
    				
        app = Sys.GetFront()
        TracePrint("读取到包名: " & app)
        FW.SetTextView "即时信息", "读取到包名: " & app, 1400, 0, 520, 30
    		
        If looptime = 80 Then 
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
    While not inWorld() and looptime < 80
        click 836,223
        Delay 500
        click 836,223
        looptime = looptime + 1
        traceprint looptime
    Wend
    
    If looptime = 80 Then 
        restartGame
    End If
    traceprint "进入游戏"
    FW.SetTextView "即时信息", "进入游戏", 1400, 0, 520, 30
  	double = 0
End Function



//点击操作
Function click(x,y)
    Touch x, y, 100
    Delay 400
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
    Delay 100
    TouchMove x2, y2, 0, 200
    Delay 100
    TouchUp 
    Delay 400
End Function


Function drag(x1,y1,x2,y2)
    TouchDown x1,y1
    Delay 200
    TouchMove x2, y2, 0, 200
    Delay 2000
    TouchUp
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

//查找图片
Function MatchPic(x1,y1,x2,y2,Pic,dirc)
dim intX,intY
FindPic x1,y1,x2,y2,"Attachment:" & Pic & ".png","000000",dirc,0.75,intX,intY
If intX > -1 And intY > -1 Then
	TracePrint intX & "," & intY
	MatchPic = True
Else 
	MatchPic = False
End If
End Function

//等待文字出现再点击
Function waitAndClick(x1, y1, x2, y2, str, x0, y0)
    dim looptime = 0,lag = 0
    While Image.OcrText(x1, y1, x2, y2, 0, 1) <> str and looptime < 50
        looptime = looptime + 1
        delay 20
    Wend
    If looptime < 50 Then 
        TracePrint "已打开：" & Image.OcrText(x1,y1,x2,y2,0,1)
        Click x0, y0
    Else 
        TracePrint "等待超5秒，已卡死"
        lag = 1
    End If

End Function

//查找文字
Function 检索文字(x1, y1, x2, y2, str)
    Dim X,Y
    X = image.OcrText(x1, y1, x2, y2, 0, 1)
    Y = InStr(1, X, str)
    If Y > 0 Then 
        检索文字 = True
    Else 
        检索文字 = False
    End If
    
End Function

//点击图片
Function clickPic(x1,y1,x2,y2,Pic, dirc)
    Dim intX, intY
    FindPic x1,y1,x2,y2,"Attachment:" & Pic & ".png","000000",dirc,0.75,intX,intY
    If intX > -1 Then
        TracePrint intX & "," & intY
        click intX,intY
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
    If (matchPointColor(1011,1746, "66676B",1) And matchPointColor(970,1585, "E7ECF0",1))_
     Or (matchPointColor(796,1746, "66676B",1) And matchPointColor(755,1585, "E7ECF0",1))_
     Or (matchPointColor(582,1746, "66676B",1) And matchPointColor(540,1585, "E7ECF0",1))_
     Or (matchPointColor(883,1717, "764010",1) And matchPointColor(980,950, "DDE6EE",1))_
     Or (matchPointColor(1015,1749, "000000",1) And matchPointColor(980,950, "DDE6EE",1)) Then
     
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
    If matchPointColor(1022, 153, "E8EBF0",1) and matchPointColor(1007,539, "E8EBF0",1)Then 
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
    If matchPointColor(218,96,"F6F6F5",1) and matchPointColor(150,73,"0D0D0D",1) Then //判定左下角菜单
        inWorld = true
        TracePrint "检测到在世界中"
        FW.SetTextView "即时信息", "检测到在世界中", 1400, 0, 520, 30
    Else 
        inWorld = False 
    End If
End Function


//地图中(是的话函数返1)
Function inMap()
    If matchPointColor(1056,668, "443A1A",1) And matchPointColor(1037,1030, "9AD1DC",1) Then 
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

Function run()
    TracePrint "******************尝试执行run*******************"
    While inFight() //在战斗中点撤离
        click 80, 880
        TracePrint "尝试结束战斗"
    Wend
    TracePrint "结束战斗"
End Function

Function settlementOver()
    TracePrint "******************尝试执行settlementOver*******************"
    While fightSettlement () //在战斗中或者战斗结算时，点撤离
        click 70, 800
        TracePrint "尝试结束结算"
        FW.SetTextView "即时信息", "尝试结束结算", 1400, 0, 520, 30
    Wend
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
        roll 911, 191, 191, 1691
        roll 911, 191, 191, 1691 //地图要划到左上角
        TracePrint "划到左上角"
        roll 119, 1711, 861, 891 //从左上角划到中间
        TracePrint "划到中间"
        FW.SetTextView "即时信息", "mapStandardization完成", 1400, 0, 520, 30
    Else 
        TracePrint "不在地图中，无法标准化"
    End If
    
End Function


//传送至城镇
// 1.新德尔斯塔
Function tpTown(n)
    TracePrint "************************************************尝试执行tpTown*************************************************"
    If inMap() Then 
        mapStandardization //先标准化方便传送操作
        Select Case n //选择传送编号
        Case 0 //新德尔斯塔
            click 488,1570
            TracePrint "新德尔斯"
            FW.SetTextView "即时信息", "前往新德尔斯", 1400, 0, 520, 30
        	
			
        Case Else
            TracePrint "未知传送点"
            Goto unknown
        End Select
        Delay 800
        slowClick 126, 1615 //确认传送操作
        click 350, 1198
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

//从逢魔地图返回城镇
Function backTown(n)
	rem start0
	moveMinimap FM(0, 0, 0), FM(0, 0, 1)
	If infight() Then 
		autokill 
		goto start0
	End If
	dim looptime = 0
	If n = 0 Then 
	slowclick FM(1, 0, 0), FM(1, 0, 1)
	While inGame() And  inWorld()
	slowclick FM(1, 0, 0), FM(1, 0, 1)
	TracePrint "返回中"
	Delay 1000
	looptime = looptime + 1
	If looptime > 30 Then 
		restartGame 
        goto start0
	End If
	Wend
	End If
	
	looptime = 0
	click 352,1078
	While inGame() And Not inWorld() //确认是否返回城镇
		click 352,1078
        TracePrint "返回中"
        Delay 1000
	 	looptime = looptime + 1
			If looptime > 30 Then 
				restartGame  
        		goto start0
			End If
    Wend
End Function

//传送到对应地区的城镇中
Function town(n)
	click 930, 1618  //打开小地图
    Delay 500
	Select Case n
		Case 0
		 If 	matchPointColor(345,510,"E1E1E1",1) and matchPointColor(360,521,"5D5D5D",1)_
		 and	matchPointColor(164,1201,"E1E1E1",1) and matchPointColor(144,1202,"151515",1) Then 
        TracePrint  "在新德尔斯塔"
        
        backWorld
        Else 
         TracePrint  "不在新德尔斯塔"
       
        backWorld
        openMap 
        tpTown(0)
        TracePrint "传送到新德尔斯塔"
        FW.SetTextView "即时信息", "传送到新德尔斯塔", 1400, 0, 520, 30
         
        End If 
	End Select
End Function

//打开地图
Function openMap()
    TracePrint "******************尝试执行openMap*******************"
    If inWorld() Then 
        TracePrint "打开地图"
        dim looptime=0
        While inGame() And Not inMap() and looptime<10
            click 145,1121
            Delay 1000
            looptime=looptime+1
        Wend
         If looptime = 10 Then 
        restartGame
    	End If
    traceprint "进入游戏"
    FW.SetTextView "即时信息", "进入游戏", 1400, 0, 520, 30
        TracePrint "地图打开成功"
        FW.SetTextView "即时信息", "地图打开成功", 1400, 0, 520, 30
        
    Else 
        TracePrint "不在世界中，无法打开地图"
        FW.SetTextView "即时信息", "不在世界中，无法打开地图", 1400, 0, 520, 30
    End If
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



 


Function readyToFight()
    TracePrint "**************readyToFight***************"
    While roundEnd()
        Delay 1000	
    Wend
End Function


Function roundEnd()
    If inFight() Then 
        If Not matchPointColor(104,1867, "868686",1) and Not matchPointColor(104,1425, "7E7E7E",1) Then 
            roundEnd = True
            //TracePrint "回合结束中，无法操作"
        Else 
            roundEnd = False
        	//TracePrint "战斗中"
        End If
        
    End If
End Function

//结束回合(持续到新的回合或者战斗结束)
Function roundOver()
    TracePrint "****************尝试执行roundOver*****************"
    If inFight() Then 
        //TracePrint "尝试结束回合"
        Click 122, 1707
        Click 122, 1707
        Click 122, 1707
       
            
        While roundEnd()  //回合结束时等待
            Delay 1000
            
        Wend    
    Else 
        //TracePrint "不在战斗中，无法结束回合！"
    End If
End Function

/*------------------------------------------------------------------------------------------*/
/*-------------------------------------战斗中操作--------------------------------------------*/
/*------------------------------------------------------------------------------------------*/
//万能使用技能(第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个)
Function Sskill(a, b, c)
 	
    TracePrint "******************尝试执行Sskill******************"
    If a = 5 Then //1号位需要换人
        xskill 1, b, c
        
    ElseIf a = 6 Then //2号位需要换人
        xskill 2, b, c
        
    ElseIf a = 7  Then //3号位需要换人
        xskill 3, b, c
        
    ElseIf a = 8  Then //4号位需要换人
        xskill 4, b, c
       
    ElseIf a = 1  Then 
        skill 1, b, c
    ElseIf a = 2 Then 
        skill 2, b, c
    ElseIf a = 3  Then 
        skill 3, b, c	
    ElseIf a = 4  Then 
        skill 4, b, c		
    End If
End Function
//换人释放技能 (第a个人, 第b个技能（平A算0技能,必杀技算5技能）, bp用c个)
Function xskill(a, b, c)
    TracePrint "******************尝试执行xskill******************"
    If inFight() Then 
        TracePrint a+4 & "号位释放" & b & "技能，消耗" & c & "bp"
        Click 962 - (a - 1) * 214, 1603//选人
        Click 122, 1707//交替
        
        If c=0 And b<>5 Then //不用bp且不用绝招时，点技能 
            click 780 - 160 * b, 1200
        ElseIf b=5 Then //用绝招时
            Click 950, 1050
            click 767,1019
            Click 288,1427
            click 962, 1603
            Delay 200
            click 1060, 400
            
        Else //用bp时，拖动技能
            roll 780 - 160 * b, 1419, 780 - 160 * b, 1419 + c * 140
        End If
        
        While inGame() And matchPointColor(287, 1592, "D3DCE0", 1)
        	click 1060,400
        Wend
        
        While (inGame() And chooseSkill(a)) or chooseSkill(a)
            click 1060,400//点一下防止技能没放出来导致卡住
        Wend
        
    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function

 
//释放技能 (第a个人, 第b个技能（平A算0技能,终结技算5技能）, bp用c个)
Function skill(a, b, c)
    TracePrint "******************尝试执行skill*******************"
    If inFight() Then 
        TracePrint a & "号位释放" & b & "技能，消耗" & c & "bp"
        
        Click 962 - (a - 1) * 214, 1603//选人
        
        If c=0 And b<>5 Then //不用bp且不用绝招时，点技能
            click 780 - 160 * b, 1200
        ElseIf b=5 Then //用绝招时
            Click 950, 1050
            click 767,1019
            Click 288,1427
            click 962, 1603
            Delay 200
            click 1060, 4000
            
        Else //用bp时，拖动技能
            roll 780 - 160 * b, 1419, 780 - 160 * b, 1419 + c * 140
        End If
        
        While inGame() And matchPointColor(287, 1592, "D3DCE0", 1)
        	click 1060,400
        Wend
        
        While (inGame() And chooseSkill(a)) or chooseSkill(1)
            //click 909,788 //点一下防止技能没放出来导致卡住
            click 1060,400
        Wend
        
    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function
//正在选择技能(是的话函数返True)（用来防止卡在选择技能界面）
Function chooseSkill(n)
    TracePrint "判断"&n&"号位是否在使用技能"
    If inFight() Then 
        If matchPointColor(1145-215*n,1620, "78390A",2) Then 
            chooseSkill = True
            TracePrint "正在选择技能"
        End If
    End If
End Function
//宠物技能  a释放的单位 b选择目标（不可选择目标技能填0） c BP数
Function cwskill(a, b,c)
    TracePrint "******************尝试执行skill*******************"
    If inFight() Then 
        If a > 4 Then 
            Click 962 - (a - 5) * 214, 1603//选人
            Click 122, 1707//交替	
        Else 
            Click 962 - (a - 1) * 214, 1603	 
        End If
        Click 950, 1050 //点头像
        click 765,1382  //点支炎兽
        If c=0 And b=0 Then //不用bp，自身技能
            click 291, 1419 //点召唤
            Delay 1000 
            click 1060, 400
            Delay 1000
        ElseIf c=0 And b <> 0 Then //不用BP，点选技能
            click 291, 1419
            Delay 1000
            Click 962 - (b - 1) * 214, 1603
            delay 1000
            click 1060, 400
            Delay 1000  
        ElseIf c <> 0 And b = 0 Then  //用BP，自身技能
            roll 620, 1040, 620, 1040 + c * 140
            Delay 200
            click 291, 1419
            delay 1000
            click 1060, 400
            Delay 1000       
        Else //用bp时，点选技能
            roll 620, 1040, 620, 1040 + c * 140
            Delay 200
            click 291, 1419
            Delay 1000
            Click 962 - (b - 1) * 214, 1603
            Delay 1000
            click 1060, 400 
            Delay 1000
        End If
        
        While inGame() And chooseSkill(a)
            //click 909,788 //点一下防止技能没放出来导致卡住
            click 1060,400
        Wend
        
    Else 
        TracePrint "不在战斗中，无法释放技能！"
    End If	
End Function

Function fulldp()
    TracePrint "******************尝试执行fulldp******************"
    If inFight() Then
        TracePrint "全员蓄力"
        click 100, 1300
    Else 
        TracePrint "不在战斗中，无法结蓄力！"
    End If
End Function



Function 战斗配置1()
    dim x=Array(),y=Array()
    readyToFight 
    Delay 5000*ReadUIConfig("战斗开场延时")
    For j = 1 To 5
        If ReadUIConfig("1宠物T" & j) Then 
            cwskill(ReadUIConfig("1释放单位T" & j)+1,ReadUIConfig("1对象T" & j) ,ReadUIConfig("1宠物BPT" & j))	
        End If
        For i = 1 To 4
            If ReadUIConfig("1" & i & "T"& j) Then 
                y(i) = ReadUIConfig("1" & i & "BPT"& j)
               
                x(i)= ReadUIConfig("1" & i & "技能T"& j)
                
                If ReadUIConfig("1全体加成T" & j) Then 
                    y(i)=0
                End If
                If ReadUIConfig("1" & i & "前后卫T" & j) = 0 Then 
                    skill i, x(i), y(i)
                Else 
                    xskill i,x(i),y(i)
                End If
            End If
		
        Next
        Delay 500
        If ReadUIConfig("技能二次确认") Then 
			For i = 1 To 4
				If not matchPointColor(1100-215*i,1800,"08154A",2) and ReadUIConfig("1" & i & "T"& j) Then
			   		skill i, x(i), y(i)
                End If
			Next
		End If
        If ReadUIConfig("1全体加成T" & j) Then 
            fulldp
        End If
        roundOver
    Next
	
	
End Function

Function 战斗配置2()
    dim x=Array(),y=Array()
    readyToFight 
    Delay 5000*ReadUIConfig("战斗开场延时")
    For j = 1 To 5
        If ReadUIConfig("2宠物T" & j) Then 
            cwskill(ReadUIConfig("2释放单位T" & j)+1,ReadUIConfig("2对象T" & j) ,ReadUIConfig("2宠物BPT" & j))	
        End If
        
        For i = 1 To 4	
            If ReadUIConfig("2" & i & "T"& j) Then 
                y(i) = ReadUIConfig("2" & i & "BPT"& j)
               
                x(i) = ReadUIConfig("2" & i & "技能T"& j)
                
                If ReadUIConfig("2全体加成T" & j) Then 
                    y(i)=0
                End If
                If ReadUIConfig("2" & i & "前后卫T" & j) = 0 Then 
                    skill i, x(i), y(i)
                Else 
                    xskill i,x(i),y(i)
			
                End If
            End If
		
        Next
        Delay 500
        If ReadUIConfig("技能二次确认") Then 
			For i = 1 To 4
				If not matchPointColor(1100-215*i,1800,"08154A",2) and ReadUIConfig("2" & i & "T"& j) Then
                    skill i, x(i), y(i)
                End If
			Next
		End If
        If ReadUIConfig("2全体加成T" & j) Then 
            fulldp
        End If
        
        
        roundOver
    Next
	
	
End Function



Function autokill()
    TracePrint"***********************尝试执行kill************************"
    While inFight()       
        readyToFight
        fastclick 95,731
        roundOver 
    Wend
    dim lp=0
    While   fightSettlement() or lp < 5
    	click 161, 1031
    	lp = lp + 1
    	TracePrint"等待结算"
    Wend
End Function

//世界中恢复状态(通行证专属)(次数可能归零,不建议使用)
Function recover()
	backWorld
    TracePrint "******************尝试执行recover*******************"
    If inWorld() Then 
        TracePrint "执行恢复"
        If matchPointColor(260,1832, "B37B55",1) Then 
            click 295,1834
            click 295,1834
            click 356,1076
            
            While inGame() And Not inWorld()
                Delay 1000
                click 356,1076
                
            Wend
            TracePrint "恢复完毕"
        Else 
            TracePrint "恢复次数不够"
        End If
    Else 
        TracePrint "不在世界中，无法恢复状态"
    End If
End Function


//前往新德尔斯塔睡觉(有通行证者不建议使用)
Function sleep()
    TracePrint "******************尝试执行sleep*******************"
    If inWorld() Then 	
        TracePrint "执行"
        openMap //打开地图
        tpTown(0) //传送至新德尔斯塔
        click 720,961 //点击旅馆
        While inGame() And Not matchPointColor(728,693, "DDE6EE",1)
            delay 1000
        Wend
        click 723,731 //点击旅馆老板
        Delay 1000
        click 322, 1198 //一直点跳过对话并确认睡觉
        click 322, 1198
        click 322, 1198
        While inGame() And Not inWorld() //不在地图中说明睡觉没成功，则等待
            Delay 1000
            click 322, 1198 //关闭睡觉成功对话框
        Wend
        TracePrint "睡觉成功"
    Else 
        TracePrint "不在世界中，无法前往旅馆睡觉"
    End If
End Function


//恢复状态(万能通用)(建议使用)(原地恢复反0,城镇恢复反1)
Function recoverAll()
    TracePrint "************************************尝试执行recoverAll*************************************"
    If inWorld() Then 
        TracePrint "执行恢复"
        If ReadUIConfig("（SP检测）恢复") and checkRN > 0 Then 
        	recoverAll = 0
        ElseIf   matchPointColor(260,1832, "B37B55",2) Then //有通行证恢复次数
            TracePrint "有恢复次数"
            recover
            recoverAll = 0
        Else  
            TracePrint "无恢复次数"
            sleep 
            recoverAll = 1
        End If	
    Else 
        TracePrint "不在世界中，无法恢复状态"
    End If
End Function
Function 精英怪()
	readyToFight
	Select Case ReadUIConfig("地区")
		Case 0
	
		If matchPointColor(988,914,"FF2DF2",1)_
		or matchPointColor(988,974,"FF2DF2",1)_
		or matchPointColor(988,1034,"FF2DF2",1)_
		or matchPointColor(988,1094,"FF2DF2",1)_
		or matchPointColor(988,1154,"FF2DF2",1) Then
			TracePrint "识别到精英怪"
			精英怪() = true
			
		End If
	End Select
End Function

Function BOSS()
	readyToFight
	Select Case ReadUIConfig("地区")
		Case 0
	
		If (matchPointColor(965,924,"B9B1C1",1) and matchPointColor(963,918,"CFB5E1",1))_
		or (matchPointColor(965,984,"B9B1C1",1) and matchPointColor(963,978,"CFB5E1",1))_
		or (matchPointColor(965,1044,"B9B1C1",1) and matchPointColor(963,1038,"CFB5E1",1))_
		or (matchPointColor(965,1104,"B9B1C1",1) and matchPointColor(963,1098,"CFB5E1",1))_
		or (matchPointColor(965,1164,"B9B1C1",1) and matchPointColor(963,1158,"CFB5E1",1)) Then
			TracePrint "识别到BOSS"
			BOSS() = true
			
		End If
	End Select
End Function
//三水家mod
Function checkRecoveryNeeded()
	checkRN = 0
	If checkBoss < 1 Then 
		FW.SetTextView "即时信息", "精英怪战斗", 1400, 0, 520, 30
	ElseIf matchPointColor(913,1719,"897650",1)_
		or matchPointColor(698,1719,"897650",1)_
		or matchPointColor(484,1719,"897650",1)_
		or matchPointColor(269,1721,"897650",1) Then
		checkRN = 1
		FW.SetTextView "即时信息", "BOSS战：蓝量充足", 1400, 0, 520, 30
	Else 
		FW.SetTextView "即时信息", "BOSS战：蓝量不足，结束后消耗恢复次数", 1400, 0, 520, 30
	End If
End Function


//v1.1 更新
//1.新增恢复功能
//2.修正最后一个坐标是BOSS时，坐标发生偏移点击不到的问题
//3.增加检测探索点是否显形的逻辑，修改后探索逻辑分三阶段， 一阶段按顺序探索所有点，
//检测到探索点已显形时，转入二阶段，只探索有效的点，三阶段查找BOSS位置。原探索
//逻辑为，一阶段遍历所有探索点，二阶段查找BOSS位置以及之前遗漏的已知探索点。
//v1.2 更新
//1.增加：无通行证小怪遇敌委托战斗
//2.战斗判断修改点位
//3.修正宠物点选技能无法选人
//4.必杀默认对1号位为释放，比如索隆的必杀，将要吃这个技能角色调整到1号位
//5.进入各种死循环时，增加重启判断

//v1.3 更新
//1.整合三水mod版SP检测恢复，按需选择
//2.为了更精确识别到点位，精度调整到0.98，战斗判断点位修改，主城判定点位修改


//检测sp版mod简要：
//本mod主要是为了改进恢复流程，能正常使用原脚本的人的队伍至少有二连战的能力，因此本修改适用于需要恢复的全部玩家
//要使用本mod内容，Boss战不得使用委托战斗，并且使用打完一次智能恢复
//原理：检测boss战蓝量剩余情况