package com.example.SpringBoot.Models;

import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Component;

@Component
public class Laptop implements Computer {
    public void compile(){
        System.out.println("Compiling in Laptop..");
    }
}
