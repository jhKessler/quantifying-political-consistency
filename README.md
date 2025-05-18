
vocabulary:

vote: Abstimmung, die komplette Abstimmung über einen Gesetzesentwurf
ballot: eine einzige Stimme, die abgegeben wird
manifesto: Wahlprogramm, das die politischen Ziele einer Partei beschreibt







pipeline:


gesetzesentwurf zusammenfassen -> änderungsanträge zusammenfassen



vote -> herausfinden über welche drucksache genau abgestimmt wird (erstgenannte drucksache)

wie? llm kriegt die erste seite und soll dann anhand einer liste der verbundenen drucksachen und deren titel herausfinden worüber abgestimmt wird, und returned dann den pfad, bzw die pfade falls mehrere drucksachen relevant sind

schauen welche art:
änderungsantrag (dann zusammenfassen von NUR dem änderungsantrag)
gesetzesentwurf (dann zusammenfassen von gesetzesentwurf)
entschließungsantrag (ignorieren, da keine rechtswirkung und schwierig zu modellieren)
beschlussempfehlung (schauen ob die empfehlung für oder gegen den gesetzesentwurf ist, dann zusammenfassen des gesetzesentwurfes und evtl negierung des ergebnisses)
antrag (wird gleich behandelt wie ein gesetzesentwurf, auch wenn es keine gesetzliche Wirkung hat)