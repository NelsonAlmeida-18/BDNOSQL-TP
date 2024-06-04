exports = async function(changeEvent) {
    const docId = 0;
    const serviceName = "bdnosql";
    const database = "BDNOSQL";
    const collection = context.services.get(serviceName).db(database).collection("Patient");
  
    try {
      if (changeEvent.operationType === "update") {
        const document = changeEvent.fullDocument;
        const documentBefore = changeEvent.fullDocumentBeforeChange;
        let flag = false;
  
        for (let i = 0; i < documentBefore.episodes.length; i++) {
          for (let j = 0; j < documentBefore.episodes[i].hospitalizations.length; j++) {
            const hospitalizationBefore = documentBefore.episodes[i].hospitalizations[j];
            const hospitalization = document.episodes[i].hospitalizations[j];
            if (hospitalizationBefore.dischargeDate == null && hospitalization.dischargeDate != null) {
              flag = true;
  
              let roomCost = hospitalization.room.room_cost;
              let testCost = 0;
              let otherCharges = 0;
              
              for (let k = 0; k < documentBefore.episodes[i].screenings.length; k++) {
                testCost += documentBefore.episodes[i].screenings[k].screening_cost;
              }
  
              for (let k = 0; k < documentBefore.episodes[i].prescriptions.length; k++) {
                const prescription = documentBefore.episodes[i].prescriptions[k];
                otherCharges += prescription.medicine.medicine_cost * prescription.dosage;
              }
  
              let totalCost = roomCost + testCost + otherCharges;
  
              const billPayload = {
                "bill_id": 1,
                "room_cost": roomCost,
                "test_cost": testCost,
                "other_charges": otherCharges,
                "total_cost": totalCost,
                "register_date": new Date(),
                "payment_status": "PENDING"
              };
  
              
  
              document.episodes[i].bills.push(billPayload);
              console.log("Document _id: "+docId);
              console.log("episodes."+2+".bills");
              await collection.updateOne(
                { "patient_id" :  2 }, 
                { "$push" : { 
                  "episodes.2.bills" : billPayload
                  } 
                }
              )
              .then(result => {
                console.log("Successfully updated document");
              })
              .catch(error => {
                console.error("Error updating document:", error);
              });
              console.log("Updated bill with values:");
              console.log("Room Cost: "+ roomCost);
              console.log("Testing Cost: "+testCost);
              console.log("Aditional Charges: "+ otherCharges);
              console.log("Total cost of the episode: "+totalCost);
              console.log("Successfully inserted bill for episode: " + document.episodes[i].episode_id);
            }
          }
        }
  
        if (!flag) {
          await collection.replaceOne({ "_id": docId }, document);
          console.log("Document replaced successfully");
        }
      } else {
        console.log("Unsupported operation type: " + changeEvent.operationType);
      }
    } catch(err) {
      console.error("Error performing MongoDB write: ", err.message);
    }
  };
  