<?php

declare(strict_types=1);

namespace App\Billing;

use InvalidArgumentException;

/**
 * Клас для обробки та розрахунку вартості замовлень клієнтів.
 */
final class OrderProcessorClean
{
    private const int CUSTOMER_REGULAR = 1;
    private const int CUSTOMER_VIP = 2;

    private const float BULK_ORDER_THRESHOLD = 1000.0;
    private const float REGULAR_BULK_DISCOUNT = 0.15;
    private const float REGULAR_BASE_DISCOUNT = 0.05;
    private const float VIP_DISCOUNT = 0.25;
    private const float EXPRESS_DELIVERY_FEE = 150.0;
    private const float VAT_MULTIPLIER = 1.20;

    /**
     * Розраховує фінальну суму замовлення з ПДВ та доставкою.
     *
     * @param int $customerType Тип клієнта (1 - звичайний, 2 - VIP).
     * @param array<int, array{price: float, quantity: int}> $items Список позицій замовлення.
     * @param bool $isExpressDelivery Чи обрано експрес-доставку.
     * @return float Підсумкова сума до сплати.
     */
    public function calculateTotal(
        int $customerType,
        array $items,
        bool $isExpressDelivery = false,
    ): float {
        $subtotal = $this->calculateSubtotal($items);
        $discountRate = $this->resolveDiscountRate($customerType, $subtotal);
        $discountedTotal = $subtotal * (1.0 - $discountRate);

        if ($isExpressDelivery) {
            $discountedTotal += self::EXPRESS_DELIVERY_FEE;
        }

        return round($discountedTotal * self::VAT_MULTIPLIER, 2);
    }

    /**
     * @param array<int, array{price: float, quantity: int}> $items
     */
    private function calculateSubtotal(array $items): float
    {
        $subtotal = 0.0;

        foreach ($items as $item) {
            if ($item['quantity'] <= 0) {
                continue;
            }

            if ($item['price'] < 0) {
                throw new InvalidArgumentException('Ціна товару не може бути від’ємною.');
            }

            $subtotal += $item['price'] * $item['quantity'];
        }

        return $subtotal;
    }

    private function resolveDiscountRate(int $customerType, float $subtotal): float
    {
        if ($customerType === self::CUSTOMER_VIP) {
            return self::VIP_DISCOUNT;
        }

        if ($customerType !== self::CUSTOMER_REGULAR) {
            return 0.0;
        }

        return $subtotal > self::BULK_ORDER_THRESHOLD
            ? self::REGULAR_BULK_DISCOUNT
            : self::REGULAR_BASE_DISCOUNT;
    }
}

