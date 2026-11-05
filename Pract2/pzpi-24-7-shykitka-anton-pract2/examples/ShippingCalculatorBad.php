<?php

declare(strict_types=1);

namespace App\Service\Shipping;

/**
 * Калькулятор доставки ДО застосування методу
 * Replace Magic Number with Symbolic Constant.
 * Проблема: числові літерали без пояснення змісту ускладнюють розуміння та супровід.
 */
class ShippingCalculatorBad
{
    public function calculateDeliveryCost(
        float $orderSubtotal,
        float $weightKg,
        int $storageDays,
    ): float {
        $cost = 0.0;

        // Якщо сума менша за 2000 грн, нараховується базовий тариф 120 грн
        if ($orderSubtotal < 2000.0) {
            $cost += 120.0;
        }

        // Якщо вага перевищує 30 кг, доплата 25 грн за кожен понаднормовий кг
        if ($weightKg > 30.0) {
            $cost += ($weightKg - 30.0) * 25.0;
        }

        // Якщо зберігання на складі понад 5 діб — пеня 40 грн за добу
        if ($storageDays > 5) {
            $cost += ($storageDays - 5) * 40.0;
        }

        // Додаємо обов'язковий страховий збір 1.5% від вартості замовлення та ПДВ 20%
        $insurance = $orderSubtotal * 0.015;

        return round(($cost + $insurance) * 1.20, 2);
    }
}

