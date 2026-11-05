<?php

declare(strict_types=1);

namespace App\Service\Refund;

/**
 * Сервіс розрахунку суми повернення коштів ПІСЛЯ застосування методу
 * Replace Nested Conditional with Guard Clauses.
 * Перевага: граничні перевірки винесені на початок методу, основний потік лінійний.
 */
final class RefundCalculatorRefactored
{
    private const int MAX_RETURN_DAYS = 14;
    private const float OPENED_ITEM_REFUND_FACTOR = 0.85;

    public function calculateRefund(
        bool $isOrderPaid,
        bool $isOrderCancelled,
        bool $isDigitalProduct,
        int $daysSincePurchase,
        float $orderTotal,
        bool $isItemOpened,
    ): float {
        if (!$isOrderPaid) {
            return 0.0;
        }

        if ($isOrderCancelled) {
            return $orderTotal;
        }

        if ($isDigitalProduct || $daysSincePurchase > self::MAX_RETURN_DAYS) {
            return 0.0;
        }

        if ($isItemOpened) {
            return round($orderTotal * self::OPENED_ITEM_REFUND_FACTOR, 2);
        }

        return $orderTotal;
    }
}

