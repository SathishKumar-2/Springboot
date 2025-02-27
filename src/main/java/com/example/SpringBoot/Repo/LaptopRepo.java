package com.example.SpringBoot.Repo;

import com.example.SpringBoot.Models.Laptop;

import org.springframework.stereotype.Repository;

@Repository
public class LaptopRepo {
    public void save(Laptop lap) {
        System.out.println("Saved in DB");
        System.out.println("Saved in DB");
    }
}
