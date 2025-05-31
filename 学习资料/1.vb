//交流群群号213459239
//分辨率1920x1080 DPI 270-320 推荐320 
//游戏内 原画，60帧，1080p，视野标准，超分辨率算法开启

Dim ambiguity =0.98
Dim app,FM=Array(),loop1=0,loop2=0,markTime,double=0
//三水MOD修改开始
Dim checkRN = 0
Dim checkBoss = 0
//三水MOD修改结束

startGame()//兼容B服和网易服，直接运行脚本可以打开游戏


FW.NewFWindow "浮窗", 0, 1050, 1920, 30
//创建文字控件
FW.Show ("浮窗")
FW.AddTextView "浮窗", "主窗口", "", 0, 0, 1400, 30
FW.AddTextView "浮窗", "即时信息", "脚本运行中", 1400, 0, 520, 30
FW.Opacity "浮窗", 0
FW.SetTextColor "主窗口", "FFFFFF"
FW.SetTextColor "即时信息", "FFFFFF"
FW.SetTextView "即时信息", "", 1400, 0, 520, 30


Select Case ReadUIConfig("地区")
    Case 0
        FM(0)={{158,520},{158,565},{146,719},{264,796},{412,887},{695,729},{690,1014},{593,1015},{592,1244},{324,1248},{326,1070},{146,1132},{148,897}}
        FM(1)={{594,677},{632,970},{602,1050},{551,775},{600,1107},{592,976},{533,1107},{563,797},{605,960},{606,1318},{599,958},{583,930},{561,1170}}
End Select

/*------------------------------------------------------------------------------------------*/
/*-------------------------------------子线程操作--------------------------------------------*/
/*------------------------------------------------------------------------------------------*/

//三水MOD修改开始
Sub 确定()
    While true
    If MatchPic(50, 491, 812, 1446, "确定", 1) Then 
         If MatchPic(245, 425, 835, 1490, "发现所有", 1) Then 
             Thread.SetShareVar "statusCheck", 1
         ElseIf MatchPic(245, 425, 835, 1490, "逢魔之主", 1) Then 
             Thread.SetShareVar "statusCheck", 2
         End If
        clickPic 50, 491, 812, 1446, "确定", 1
    End If
    clickPic 330,890,739,1377, "重试", 1
    Delay 500
    loop1 = Thread.GetShareVar("loop1")
    loop2 = Thread.GetShareVar("loop2")
    markTime = Thread.GetShareVar("markTime")

    FW.SetTextView ("主窗口", "运行" & Round(TickCount()/ 60000, 1) & "分钟，已完成" & loop1 & "次，失败" & loop2 &"次，本次计时：" & Round((TickCount() - markTime) / 60000, 1) & "分钟，场均" & Round(markTime / 60000 / loop1, 1) & "分钟。" , 0, 0, 1200, 30)//更新主显示
    
    Wend
End Sub
Thread.Start(确定)
Sub bloodMonitor()
    dim blood,b1=0,b2=0,b3=0,b4=0
    dim checkRN = Thread.GetShareVar("checkRN")
    While checkRN =1
        b1 = isBloodLow(954, b1)
        b2 = isBloodLow(740, b2)
        b3 = isBloodLow(526, b3)
        b4 = isBloodLow(311, b4)
        checkRN = Thread.GetShareVar("checkRN")
    Wend
    blood = b1 + b2 + b3 + b4
    If blood > 0 Then 
    Thread.SetShareVar"checkRN", 2    
    End If
End Sub

Sub 三水modder()    
    FW.NewFWindow "三水mod", 0,300,600,300
    FW.Show ("三水mod")
    FW.Opacity "三水mod", 0
    FW.AddTextView "三水mod", "当前挑战", "读取状态中", 0, 0, 600, 50
    FW.AddTextView "三水mod", "恢复状态", "读取状态中", 0, 50, 600, 50
    FW.SetTextColor "当前挑战", "FFFF33"
    FW.SetTextColor "恢复状态", "FFFF33"
    dim 难度 = ReadUIConfig("难度") + 1
    dim 地区 = ReadUIConfig("地区")
    Select Case 地区
        Case 0
        FW.SetTextView "当前挑战", "地区：新德尔斯塔；难度：深度"& 难度, 0, 0, 600, 50
    End Select
    If ReadUIConfig("（SP检测）恢复") and ReadUIConfig("打完一次恢复")_
        or ReadUIConfig("（SP检测）恢复") Then
        FW.SetTextView "恢复状态","已开启三水mod智能恢复", 0, 50, 600, 50
    ElseIf ReadUIConfig("打完一次恢复") Then
        FW.SetTextView "恢复状态","已开启打完一轮自动恢复", 0, 50, 600, 50
    Else 
        FW.SetTextView "恢复状态","未开启任何恢复", 0, 50, 600, 50
    End If
    dim tp=0,结晶=0
    Dim 加护上限 = 0,结晶上限 = 0
    If ReadUIConfig("启动收益计算") Then     
        Thread.SetShareVar "gain",0
        FW.AddTextView "三水mod", "TP收益", "个人加护点收益：", 0, 100, 600, 50
        FW.AddTextView "三水mod", "结晶收益", "个人结晶收益：", 0, 150, 600, 50
        FW.SetTextColor "TP收益", "FF6600"
        FW.SetTextColor "结晶收益", "FF6600"
        If ReadUIConfig("加护点上限预警") Then 
            FW.AddTextView "三水mod", "TP预警", "加护点上限预警已开启", 0, 200, 600, 50
            FW.SetTextColor "TP预警", "00FF00"
            加护上限 = 9999 - ReadUIConfig("个人加护点基础值")
        End If
        If ReadUIConfig("结晶刷满提醒") Then 
            FW.AddTextView "三水mod", "结晶预警", "结晶刷满提醒已开启", 0, 250, 600, 50
            FW.SetTextColor "结晶预警", "00FF00"
            结晶上限 = ReadUIConfig("需要的结晶数量") + 0
        End If
        While true
            FW.SetTextView  "TP收益", "个人加护点收益：" & tp, 0, 100, 600, 50
            FW.SetTextView  "结晶收益", "个人结晶收益："& 结晶, 0, 150, 600, 50
            Delay 1000
            If Thread.GetShareVar("gain") = 1 Then
                tp = tp + 30
                结晶 = 结晶 + 3
                TracePrint "计算gain为1,tp=" & tp & "结晶等于="  & 结晶 
                Thread.SetShareVar "gain",0
            End If
            If Thread.GetShareVar("gain") = 2 Then 
                tp = tp + 30
                结晶 = 结晶 + 5 * (难度 + 地区)
                TracePrint "计算gain为2,tp=" & tp & "结晶等于="  & 结晶     
                Thread.SetShareVar "gain",0
            End If
            If ReadUIConfig("加护点上限预警") and tp > 加护上限 Then 
                FW.SetTextView "TP预警", "已达到加护点上限", 0, 200, 600, 50
                FW.SetTextColor "TP预警", "00FFFF"
            End If
            If ReadUIConfig("结晶刷满提醒") and 结晶 > 结晶上限 Then 
                FW.SetTextView "结晶预警", "已达到结晶上限", 0, 250, 600, 50
                FW.SetTextColor "结晶预警", "00FFFF"
            End If
        Wend
    End If
End Sub

//三水MOD修改结束

/*------------------------------------------------------------------------------------------*/
/*-------------------------------------主要流程---------------------------------------------*/
/*------------------------------------------------------------------------------------------*/


逢魔 ReadUIConfig("难度"),ReadUIConfig("地区")

function 逢魔(难度,地区)
    dim lp = 0
    If ReadUIConfig("mod启动") Then 
        Thread.Start(三水modder)
    End If
    
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
    FW.SetTextView ("即时信息", "开始逢魔", 1400, 0, 420, 30)
   
    Rem start1  

    click FM(1,0,0),FM(1,0,1)
    Delay 1000
    
    
    
    markTime = TickCount()
    Thread.SetShareVar "loop1",loop1
    Thread.SetShareVar "loop2",loop2
    Thread.SetShareVar "markTime",markTime  
      FW.SetTextView ("主窗口", "运行" & Round(TickCount()/ 60000, 1) & "分钟，已完成" & loop1 & "次，失败" & loop2 &"次，本次计时：" & Round((TickCount() - markTime) / 60000, 1) & "分钟，场均" & Round(markTime / 60000 / loop1, 1) & "分钟。" , 0, 0, 1200, 30)//更新主显示
    
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
    FW.SetTextView ("即时信息", "开始", 1400, 0, 420, 30)
    Delay 2000
    FW.SetTextView ("即时信息", "进入地图", 1400, 0, 420, 30)
    
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

    dim A=Array(),b=0,m=0,k,n=0,c=0,j
    //三水MOD修改开始
    checkBoss = 0
    Thread.SetShareVar "statusCheck", 0
    //三水MOD修改结束
    //一阶段
    TracePrint "一阶段"
    For j = 1 To 12
        Rem start0
        
       // FW.SetTextView ("主窗口", "运行" & Round(TickCount()/ 60000, 1) & "分钟，已完成" & loop1 & "次，失败" & loop2 &"次，本次计时：" & Round((TickCount() - markTime) / 60000, 1) & "分钟，场均" & Round(markTime/ 60000 / loop1, 1) & "分钟。" , 0, 0, 1000, 30)
        
        //小boss战斗
        If inFight() and j + m > 1 Then 
            FW.SetTextView ("即时信息", "战斗中", 1400, 0, 420, 30)
            
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
            
            FW.SetTextView "即时信息", "战斗结束", 1400, 0, 520, 30
            Thread.SetShareVar "gain", 1
            TracePrint "检测gain的数值为"& Thread.GetShareVar("gain")
            b = 1
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
        
        TracePrint "等待返回世界++"
        While inGame() and not inWorld()
            If inFight() Then 
            Goto start0
            End If
            click 726,1410
        Wend
        If Thread.GetShareVar("statusCheck") > 0 Then 
            Exit For
        End If
        //移动到探索点
        moveMinimap FM(0, j, 0), FM(0, j, 1)
        
        //跳转2阶段逻辑：检测右上角的小地图自身位置周围是否是显形的，存在逻辑漏洞 
        //If matchPointColor(874, 1618, "9E66BD", 30) or matchPointColor(874, 1618, "9965BA", 30) Then 
        //TracePrint "原有逻辑生效++"
        //    Exit For
        //End If
        
        //点击探索点
        slowClick FM(1,j, 0), FM(1,j, 1)
        Delay 1000    
        
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
    
    //记录显性的位置到数组中
    For i = j To 12
               If matchPointColor(FM(0,i, 0), FM(0,i, 1), "9E66BD", 50) or matchPointColor(FM(0,i, 0), FM(0,i, 1), "9965BA", 50)  Then 
                   TracePrint "已知探索地： " & i
                   A(c) = i
                   c = c + 1
               End If
       Next
           
       backWorld
       m = 0
           
    For i = 0 To UBOUND(A)
        //考虑转移到外面 
        Rem start1
        
        
        //小boss战斗
        If inFight() and i+m>0 Then 
            FW.SetTextView "即时信息", "战斗中", 1400, 0, 420, 30
            
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
            
            FW.SetTextView "即时信息", "战斗结束", 1400, 0, 420, 30
            Thread.SetShareVar "gain", 1
            TracePrint "检测gain的数值为"& Thread.GetShareVar("gain")
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
        
           TracePrint "等待返回世界++"
        While inGame() and not inWorld()
            If inFight() Then 
            Goto start1
            End If
            click 726,1410
        Wend
        
        If Thread.GetShareVar("statusCheck") = 2 Then 
            Exit For
        End If
           
           moveMinimap FM(0, A(i), 0), FM(0, A(i), 1)
           
           slowClick FM(1,A(i), 0), FM(1,A(i), 1)
        Delay 2000
        
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
    
    //寻找boss的位置
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
        FW.SetTextView "即时信息", "战斗中", 1400, 0, 520, 30
        checkBoss = 1
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
        //三水MOD修改开始
        If checkRN = 1 Then
            FW.SetTextView "即时信息", "判断战斗状态中", 1400, 0, 520, 30
            checkRN = 3
            Thread.SetShareVar "checkRN", checkRN
            delay 1000
            If Thread.GetShareVar("checkRN") = 3 Then
                FW.SetTextView "即时信息", "BOSS战：血量蓝量充足,不恢复", 1400, 0, 520, 30
                checkRN =1
            Else 
                 FW.SetTextView "即时信息", "BOSS战：血量不足，结束后消耗恢复次数", 1400, 0, 520, 30
                 checkRN = 0
            End If 
        ElseIf checkRN = 0 and ReadUIConfig("（SP检测）恢复") Then
            FW.SetTextView "即时信息", "BOSS战：蓝量不足，结束后消耗恢复次数", 1400, 0, 520, 30
        Else
            FW.SetTextView "即时信息", "BOSS战：战斗结束", 1400, 0, 520, 30
        End If
        Thread.SetShareVar "gain", 2
        TracePrint "检测gain的数值为"& Thread.GetShareVar("gain")
        //matchPointColor(913,1719,"1",1)
        //三水MOD修改结束
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





/*------------------------------------------------------------------------------------------*/
/*-------------------------------------必要功能函数------------------------------------------*/
/*------------------------------------------------------------------------------------------*/


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



//点