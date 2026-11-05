<?php

declare(strict_types=1);

namespace App\Service\Refund;

/**
 * Сервіс розрахунку суми повернення коштів ДО застосування методу
 * Replace Nested Conditional with Guard Clauses.
 * Проблема: глибока вкладеність умовних конструкцій if-else (Arrow Anti-Pattern).
 */
class RefundCalculatorBad
{
    public function calculateRefund(
        bool $isOrderPaid,
        bool $isOrderCancelled,
        bool $isDigitalProduct,
        int $daysSincePurchase,
        float $orderTotal,
        bool $isItemOpened,
    ): float {
        $refundAmount = 0.0;

        if ($isOrderPaid) {
            if (!$isOrderCancelled) {
                if (!$isDigitalProduct) {
                    if ($daysSincePurchase <= 14) {
                        if ($isItemOpened) {
                            // Якщо пакування розкрито, утримується сервісний збір 15%
                            $refundAmount = round($orderTotal * 0.85, 2);
                        } else {
                            // Повне відшкодування вартості замовлення
                            $refundAmount = $orderTotal;
                        }
                    } else {
                        $refundAmount = 0.0;
                    }
                } else {
                    $refundAmount = 0.0;
                }
            } else {
                $refundAmount = $orderTotal;
            }
        } else {
            $refundAmount = 0.0;
        }

        return $refundAmount;
    }
}

