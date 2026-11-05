<?php

declare(strict_types=1);

namespace Tests\Unit\Billing;

use App\Billing\OrderProcessorClean;
use PHPUnit\Framework\TestCase;

/**
 * Модульні тести для перевірки коректності розрахунку вартості замовлення.
 */
final class OrderProcessorTest extends TestCase
{
    private OrderProcessorClean $processor;

    protected function setUp(): void
    {
        $this->processor = new OrderProcessorClean();
    }

    public function testCalculateTotalForVipCustomerWithExpressDelivery(): void
    {
        // Arrange (Підготовка даних)
        $items = [
            ['price' => 500.0, 'quantity' => 2],
        ];

        // Act (Виконання дії)
        $actualTotal = $this->processor->calculateTotal(
            customerType: 2,
            items: $items,
            isExpressDelivery: true,
        );

        // Assert (Перевірка результату: (1000 * 0.75 + 150) * 1.2 = 1080.0)
        self::assertSame(1080.0, $actualTotal);
    }
}

