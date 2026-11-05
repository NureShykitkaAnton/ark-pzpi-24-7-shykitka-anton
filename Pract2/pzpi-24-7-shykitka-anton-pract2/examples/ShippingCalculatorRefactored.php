<?php

declare(strict_types=1);

namespace App\Service\Shipping;

/**
 * Калькулятор доставки ПІСЛЯ застосування методу
 * Replace Magic Number with Symbolic Constant.
 * Перевага: усі бізнес-пороги і тарифи винесені у самодокументовані константи класу.
 */
final class ShippingCalculatorRefactored
{
    public const float FREE_SHIPPING_THRESHOLD_UAH = 2000.0;
    public const float BASE_DELIVERY_FEE_UAH = 120.0;

    public const float MAX_STANDARD_WEIGHT_KG = 30.0;
    public const float OVERWEIGHT_FEE_PER_KG_UAH = 25.0;

    public const int FREE_STORAGE_DAYS = 5;
    public const float STORAGE_PENALTY_PER_DAY_UAH = 40.0;

    public const float INSURANCE_RATE = 0.015;
    public const float VAT_MULTIPLIER = 1.20;

    public function calculateDeliveryCost(
        float $orderSubtotal,
        float $weightKg,
        int $storageDays,
    ): float {
        $deliveryCost = 0.0;

        if ($orderSubtotal < self::FREE_SHIPPING_THRESHOLD_UAH) {
            $deliveryCost += self::BASE_DELIVERY_FEE_UAH;
        }

        if ($weightKg > self::MAX_STANDARD_WEIGHT_KG) {
            $overweightKg = $weightKg - self::MAX_STANDARD_WEIGHT_KG;
            $deliveryCost += $overweightKg * self::OVERWEIGHT_FEE_PER_KG_UAH;
        }

        if ($storageDays > self::FREE_STORAGE_DAYS) {
            $extraStorageDays = $storageDays - self::FREE_STORAGE_DAYS;
            $deliveryCost += $extraStorageDays * self::STORAGE_PENALTY_PER_DAY_UAH;
        }

        $insuranceFee = $orderSubtotal * self::INSURANCE_RATE;

        return round(($deliveryCost + $insuranceFee) * self::VAT_MULTIPLIER, 2);
    }
}

