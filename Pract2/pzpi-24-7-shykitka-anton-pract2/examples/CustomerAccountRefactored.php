<?php

declare(strict_types=1);

namespace App\Domain\Billing;

use DomainException;
use InvalidArgumentException;

/**
 * Клас рахунку клієнта ПІСЛЯ застосування методу Encapsulate Field.
 * Поля інкапсульовані (private), доступ і зміна стану контролюються методами.
 */
final class CustomerAccountRefactored
{
    private string $ownerEmail;
    private float $balance;
    private int $bonusPoints = 0;
    private bool $isFrozen = false;

    public function __construct(string $ownerEmail, float $initialBalance = 0.0)
    {
        $this->setOwnerEmail($ownerEmail);
        if ($initialBalance < 0.0) {
            throw new InvalidArgumentException('Початковий баланс не може бути від’ємним.');
        }
        $this->balance = $initialBalance;
    }

    public function getOwnerEmail(): string
    {
        return $this->ownerEmail;
    }

    public function setOwnerEmail(string $ownerEmail): void
    {
        if (!filter_var($ownerEmail, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException('Некоректний формат електронної пошти.');
        }
        $this->ownerEmail = $ownerEmail;
    }

    public function getBalance(): float
    {
        return $this->balance;
    }

    public function getBonusPoints(): int
    {
        return $this->bonusPoints;
    }

    public function isFrozen(): bool
    {
        return $this->isFrozen;
    }

    public function freeze(): void
    {
        $this->isFrozen = true;
    }

    public function deposit(float $amount): void
    {
        if ($amount <= 0.0) {
            throw new InvalidArgumentException('Сума поповнення повинна бути більшою за нуль.');
        }
        $this->balance = round($this->balance + $amount, 2);
    }

    public function withdraw(float $amount): void
    {
        if ($this->isFrozen) {
            throw new DomainException('Операції заблоковано: рахунок заморожено.');
        }
        if ($amount <= 0.0) {
            throw new InvalidArgumentException('Сума списання повинна бути більшою за нуль.');
        }
        if ($amount > $this->balance) {
            throw new DomainException('Недостатньо коштів на рахунку для списання.');
        }
        $this->balance = round($this->balance - $amount, 2);
    }

    public function addBonusPoints(int $points): void
    {
        if ($points <= 0) {
            throw new InvalidArgumentException('Кількість бонусів має бути додатною.');
        }
        $this->bonusPoints += $points;
    }
}

