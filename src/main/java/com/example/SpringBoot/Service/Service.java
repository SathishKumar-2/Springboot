package com.example.SpringBoot.Service;

import com.example.SpringBoot.Models.Laptop;
import com.example.SpringBoot.Repo.LaptopRepo;
import org.springframework.beans.factory.annotation.Autowired;

@org.springframework.stereotype.Service
public class Service {
    @Autowired
    private LaptopRepo laptopRepo;

    public void addLaptop(Laptop lap) {
        // hi hell
        laptopRepo.save(lap);
        laptopRepo.save(lap);
    }
}
