<?php

declare(strict_types=1);

namespace App\Service;

use App\Contract\DiscountPolicyInterface;
use App\Model\Order;
use InvalidArgumentException;

/**
 * Сервіс розрахунку вартості замовлення згідно зі стандартами PSR-1 та PSR-12.
 */
final class OrderServiceClean
{
    public const float DEFAULT_TAX_RATE = 0.20;
    private const int MIN_ORDER_ITEMS = 1;

    public function __construct(
        private readonly DiscountPolicyInterface $discountPolicy,
        private readonly float $taxRate = self::DEFAULT_TAX_RATE,
    ) {
    }

    /**
     * Обчислює підсумкову вартість замовлення з урахуванням знижки та податку.
     *
     * @param Order $order Об'єкт замовлення клієнта.
     * @return float Підсумкова сума до сплати.
     * @throws InvalidArgumentException Якщо замовлення не містить товарів.
     */
    public function calculateFinalTotal(Order $order): float
    {
        if ($order->getItemsCount() < self::MIN_ORDER_ITEMS) {
            throw new InvalidArgumentException('Замовлення повинно містити щонайменше один товар.');
        }

        $subtotal = $order->getSubtotal();
        $discountAmount = $this->discountPolicy->calculateDiscount($order);
        $taxableAmount = max(0.0, $subtotal - $discountAmount);

        return round($taxableAmount * (1 + $this->taxRate), 2);
    }
}

