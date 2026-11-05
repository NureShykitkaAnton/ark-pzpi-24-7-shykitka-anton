<?php

declare(strict_types=1);

namespace App\Domain\Billing;

/**
 * Клас рахунку клієнта ДО застосування методу Encapsulate Field.
 * Проблема: публічні поля дозволяють змінювати стан об'єкта напряму без валідації.
 */
class CustomerAccountBad
{
    public string $ownerEmail;
    public float $balance = 0.0;
    public int $bonusPoints = 0;
    public bool $isFrozen = false;

    public function __construct(string $ownerEmail, float $initialBalance = 0.0)
    {
        $this->ownerEmail = $ownerEmail;
        $this->balance = $initialBalance;
    }
}

// Приклад небезпечного використання у клієнтському коді:
// $account = new CustomerAccountBad('student@nure.ua', 500.0);
// $account->isFrozen = true;
// $account->balance -= 1200.0; // Баланс став -700.0 попри заморожений рахунок!
// $account->bonusPoints = -50; // Некоректне від'ємне значення бонусів!

