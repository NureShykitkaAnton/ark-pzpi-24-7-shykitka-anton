<?php
class ord_proc {
    public $d = 0;
    function calc($u, $arr, $f) {
        $s = 0;
        for($i=0;$i<count($arr);$i++){
            if($arr[$i]['q']>0){
                $s += $arr[$i]['p'] * $arr[$i]['q']; // додаємо ціну
            }
        }
        // перевірка типу
        if($u == 1){
            if($s > 1000){
                $s = $s - ($s * 0.15);
            } else {
                $s = $s - ($s * 0.05);
            }
        } elseif($u == 2) {
            $s = $s - ($s * 0.25);
        }
        if($f == true) $s += 150;
        return $s * 1.2;
    }
}
?>

