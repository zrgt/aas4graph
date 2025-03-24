CREATE (root:RootNode {title:'EmptyNode'})
CREATE (assetinformationfacfaf:AssetInformation {asset_kind:'TYPE', asset_type:'Type', global_asset_id:'https://admin-shell.io/idta/asset/DigitalNameplate/2/0'})

CREATE (assetadministrationshella73cea:AssetAdministrationShell:Identifiable:Referable {id_short:'DigitalNameplateAAS', id_:'https://admin-shell.io/idta/aas/DigitalNameplate/2/0'})
CREATE (assetadministrationshella73cea)-[:asset_information]->(assetinformationfacfaf)

CREATE (langstring99df2a:LangString {lcode:'en', value:'Contains the nameplate information attached to the product'})

CREATE (langstring91914a:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61987#ABN590#001 URI of product instance '})

CREATE (qualifier3c147c:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (propertye7d1d7:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'URIOfTheProduct', value_type:'str', value:'https://www.domain-abc.com/Model-Nr-1234/Serial-Nr-5678'})
CREATE (propertye7d1d7)-[:description]->(langstring91914a)
CREATE (propertye7d1d7)-[:qualifier]->(qualifier3c147c)

CREATE (langstring45e703:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61987#ABA565#007 manufacturer Note: mandatory property according to EU Machine Directive 2006/42/EC. '})

CREATE (qualifier25a011:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (langstringc5e483:LangString {lcode:'de', value:'Muster AG'})

CREATE (multilanguageproperty83daf9:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'ManufacturerName'})
CREATE (multilanguageproperty83daf9)-[:description]->(langstring45e703)
CREATE (multilanguageproperty83daf9)-[:qualifier]->(qualifier25a011)
CREATE (multilanguageproperty83daf9)-[:value]->(langstringc5e483)

CREATE (langstring7ce508:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61987#ABA567#007 name of product Note: Short designation of the product is meant. Note: mandatory property according to EU Machine Directive 2006/42/EC. '})

CREATE (qualifier0bc8e8:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (langstringafd826:LangString {lcode:'en', value:'ABC-123'})

CREATE (multilanguageproperty56e0db:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'ManufacturerProductDesignation'})
CREATE (multilanguageproperty56e0db)-[:description]->(langstring7ce508)
CREATE (multilanguageproperty56e0db)-[:qualifier]->(qualifier0bc8e8)
CREATE (multilanguageproperty56e0db)-[:value]->(langstringafd826)

CREATE (langstringd45bca:LangString {lcode:'en', value:'The SMC “ContactInformation” contains information on how to contact the manufacturer or an authorised service provider, e.g. when a maintenance service is required. Note: physical address is a mandatory property according to EU Machine Directive 2006/42/EC'})

CREATE (qualifier9f878d:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (langstringbc3f61:LangString {lcode:'en', value:'enumeration: 0173-1#07-AAS927#001 (administrativ contact), 0173-1#07-AAS928#001 (commercial contact), 0173-1#07-AAS929#001 (other contact), 0173-1#07-AAS930#001 (hazardous goods contact), 0173-1#07-AAS931#001 (technical contact). Note: the above mentioned ECLASS enumeration should be declared as “open” for further addition. ECLASS enumeration IRDI is preferable. If no IRDI available, custom input as String may also be accepted.'})

CREATE (qualifierde6048:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (property6c4a75:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'RoleOfContactPerson', value_type:'str', value:'0173-1#07-AAS931#001'})
CREATE (property6c4a75)-[:description]->(langstringbc3f61)
CREATE (property6c4a75)-[:qualifier]->(qualifierde6048)

CREATE (langstringbe78d2:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61360_4#ADA005#001 country code. country codes defined accord. to DIN EN ISO 3166-1 alpha-2 codes. Mandatory property according to EU Machine Directive 2006/42/EC. Recommendation: property declaration as MLP is required by its semantic definition. As the property value is language independent, users are recommended to provide maximal 1 string in any language of the user’s choice.'})

CREATE (qualifieraa6304:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (langstring45cbbe:LangString {lcode:'en', value:'DE'})

CREATE (multilanguageproperty64c788:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'NationalCode'})
CREATE (multilanguageproperty64c788)-[:description]->(langstringbe78d2)
CREATE (multilanguageproperty64c788)-[:qualifier]->(qualifieraa6304)
CREATE (multilanguageproperty64c788)-[:value]->(langstring45cbbe)

CREATE (langstring97c108:LangString {lcode:'en', value:'Note: language codes defined accord. to ISO 639-1. Note: as per ECLASS definition, Expression and representation of thoughts, information, feelings, ideas through characters.'})

CREATE (qualifier0ba4ed:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToMany', kind:'CONCEPT_QUALIFIER'})

CREATE (property65b3b1:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'Language', value_type:'str', value:'de'})
CREATE (property65b3b1)-[:description]->(langstring97c108)
CREATE (property65b3b1)-[:qualifier]->(qualifier0ba4ed)

CREATE (langstringb9f540:LangString {lcode:'en', value:'Note: notation accord. to ISO 8601 Note: for time in UTC the zone designator “Z” is to be used'})

CREATE (qualifier22842f:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (propertye676d2:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'TimeZone', value_type:'str', value:'Z'})
CREATE (propertye676d2)-[:description]->(langstringb9f540)
CREATE (propertye676d2)-[:qualifier]->(qualifier22842f)

CREATE (langstring175c9b:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61987#ABA129#001 city/town. Mandatory property according to EU Machine Directive 2006/42/EC.'})

CREATE (qualifier5b8036:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (langstring643021:LangString {lcode:'de', value:'Musterstadt'})

CREATE (multilanguageproperty4fe176:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'CityTown'})
CREATE (multilanguageproperty4fe176)-[:description]->(langstring175c9b)
CREATE (multilanguageproperty4fe176)-[:qualifier]->(qualifier5b8036)
CREATE (multilanguageproperty4fe176)-[:value]->(langstring643021)

CREATE (qualifiere99e6a:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (langstring073c8e:LangString {lcode:'en', value:'ABC Company'})

CREATE (multilanguagepropertyc52734:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'Company'})
CREATE (multilanguagepropertyc52734)-[:qualifier]->(qualifiere99e6a)
CREATE (multilanguagepropertyc52734)-[:value]->(langstring073c8e)

CREATE (qualifier415731:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (langstringee1278:LangString {lcode:'de', value:'Vertrieb'})

CREATE (multilanguageproperty9095b4:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'Department'})
CREATE (multilanguageproperty9095b4)-[:qualifier]->(qualifier415731)
CREATE (multilanguageproperty9095b4)-[:value]->(langstringee1278)

CREATE (qualifier930024:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (langstring54b3c5:LangString {lcode:'en', value:'Recommendation: property declaration as MLP is required by its semantic definition. As the property value is language independent, users are recommended to provide maximal 1 string in any language of the user’s choice.'})

CREATE (qualifier5cbe50:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (langstring2aafe1:LangString {lcode:'en', value:'+491234567890'})

CREATE (multilanguageproperty7b5420:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'TelephoneNumber'})
CREATE (multilanguageproperty7b5420)-[:description]->(langstring54b3c5)
CREATE (multilanguageproperty7b5420)-[:qualifier]->(qualifier5cbe50)
CREATE (multilanguageproperty7b5420)-[:value]->(langstring2aafe1)

CREATE (langstringba3ebc:LangString {lcode:'en', value:' enumeration: 0173-1#07-AAS754#001 (office), 0173-1#07-AAS755#001 (office mobile), 0173-1#07-AAS756#001 (secretary), 0173-1#07-AAS757#001 (substitute), 0173-1#07-AAS758#001 (home), 0173-1#07-AAS759#001 (private mobile)'})

CREATE (qualifiercb52b3:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (property14e9df:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'TypeOfTelephone', value_type:'str', value:'0173-1#07-AAS754#001'})
CREATE (property14e9df)-[:description]->(langstringba3ebc)
CREATE (property14e9df)-[:qualifier]->(qualifiercb52b3)

CREATE (qualifier303fd2:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (langstringdb2d43:LangString {lcode:'de', value:'Montag – Freitag 08:00 bis 16:00'})

CREATE (multilanguagepropertyeb59ba:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'AvailableTime'})
CREATE (multilanguagepropertyeb59ba)-[:qualifier]->(qualifier303fd2)
CREATE (multilanguagepropertyeb59ba)-[:value]->(langstringdb2d43)

CREATE (submodelelementcollectione44334:SubmodelElementCollection:SubmodelElement:Referable:Qualifiable {id_short:'Phone'})
CREATE (submodelelementcollectione44334)-[:qualifier]->(qualifier930024)
CREATE (submodelelementcollectione44334)-[:value]->(multilanguageproperty7b5420)
CREATE (submodelelementcollectione44334)-[:child]->(multilanguageproperty7b5420)
CREATE (submodelelementcollectione44334)-[:ids_TelephoneNumber]->(multilanguageproperty7b5420)
CREATE (submodelelementcollectione44334)-[:value]->(property14e9df)
CREATE (submodelelementcollectione44334)-[:child]->(property14e9df)
CREATE (submodelelementcollectione44334)-[:ids_TypeOfTelephone]->(property14e9df)
CREATE (submodelelementcollectione44334)-[:value]->(multilanguagepropertyeb59ba)
CREATE (submodelelementcollectione44334)-[:child]->(multilanguagepropertyeb59ba)
CREATE (submodelelementcollectione44334)-[:ids_AvailableTime]->(multilanguagepropertyeb59ba)

CREATE (qualifierc2e3bb:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (qualifier80ba70:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (property9fb0f0:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'EmailAddress', value_type:'str', value:'email@muster-ag.de'})
CREATE (property9fb0f0)-[:qualifier]->(qualifier80ba70)

CREATE (langstring2de5cb:LangString {lcode:'en', value:'Recommendation: property declaration as MLP is required by its semantic definition. As the property value is language independent, users are recommended to provide maximal 1 string in any language of the user’s choice.'})

CREATE (qualifierc7b702:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (multilanguageproperty2ccb7e:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'PublicKey'})
CREATE (multilanguageproperty2ccb7e)-[:description]->(langstring2de5cb)
CREATE (multilanguageproperty2ccb7e)-[:qualifier]->(qualifierc7b702)

CREATE (langstring32740a:LangString {lcode:'en', value:'enumeration: 0173-1#07-AAS754#001 (office), 0173-1#07-AAS756#001 (secretary), 0173-1#07-AAS757#001 (substitute), 0173-1#07-AAS758#001 (home)'})

CREATE (qualifier1a2130:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (property787b63:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'TypeOfEmailAddress', value_type:'str', value:'0173-1#07-AAS754#001'})
CREATE (property787b63)-[:description]->(langstring32740a)
CREATE (property787b63)-[:qualifier]->(qualifier1a2130)

CREATE (qualifierb3e448:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (multilanguageproperty9caa30:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'TypeOfPublicKey'})
CREATE (multilanguageproperty9caa30)-[:qualifier]->(qualifierb3e448)

CREATE (submodelelementcollectionacc736:SubmodelElementCollection:SubmodelElement:Referable:Qualifiable {id_short:'Email'})
CREATE (submodelelementcollectionacc736)-[:qualifier]->(qualifierc2e3bb)
CREATE (submodelelementcollectionacc736)-[:value]->(property9fb0f0)
CREATE (submodelelementcollectionacc736)-[:child]->(property9fb0f0)
CREATE (submodelelementcollectionacc736)-[:ids_EmailAddress]->(property9fb0f0)
CREATE (submodelelementcollectionacc736)-[:value]->(multilanguageproperty2ccb7e)
CREATE (submodelelementcollectionacc736)-[:child]->(multilanguageproperty2ccb7e)
CREATE (submodelelementcollectionacc736)-[:ids_PublicKey]->(multilanguageproperty2ccb7e)
CREATE (submodelelementcollectionacc736)-[:value]->(property787b63)
CREATE (submodelelementcollectionacc736)-[:child]->(property787b63)
CREATE (submodelelementcollectionacc736)-[:ids_TypeOfEmailAddress]->(property787b63)
CREATE (submodelelementcollectionacc736)-[:value]->(multilanguageproperty9caa30)
CREATE (submodelelementcollectionacc736)-[:child]->(multilanguageproperty9caa30)
CREATE (submodelelementcollectionacc736)-[:ids_TypeOfPublicKey]->(multilanguageproperty9caa30)

CREATE (langstringdede96:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61987#ABA286#001 street. Mandatory property according to EU Machine Directive 2006/42/EC'})

CREATE (qualifierd9e27a:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (langstringdfa93a:LangString {lcode:'de', value:'Musterstraße 1'})

CREATE (multilanguageproperty0b836c:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'Street'})
CREATE (multilanguageproperty0b836c)-[:description]->(langstringdede96)
CREATE (multilanguageproperty0b836c)-[:qualifier]->(qualifierd9e27a)
CREATE (multilanguageproperty0b836c)-[:value]->(langstringdfa93a)

CREATE (langstringea15d8:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61987#ABA281#001 ZIP/Postal code. Mandatory property according to EU Machine Directive 2006/42/EC. Recommendation: property declaration as MLP is required by its semantic definition. As the property value is language independent, users are recommended to provide maximal 1 string in any language of the user’s choice.'})

CREATE (qualifier67d0fa:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (langstring08ab3a:LangString {lcode:'de', value:'12345'})

CREATE (multilanguageproperty3e36a1:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'Zipcode'})
CREATE (multilanguageproperty3e36a1)-[:description]->(langstringea15d8)
CREATE (multilanguageproperty3e36a1)-[:qualifier]->(qualifier67d0fa)
CREATE (multilanguageproperty3e36a1)-[:value]->(langstring08ab3a)

CREATE (qualifier377fb8:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (langstringcbe8c3:LangString {lcode:'en', value:'PF 1234'})

CREATE (multilanguagepropertyb61a88:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'POBox'})
CREATE (multilanguagepropertyb61a88)-[:qualifier]->(qualifier377fb8)
CREATE (multilanguagepropertyb61a88)-[:value]->(langstringcbe8c3)

CREATE (langstring5213d1:LangString {lcode:'en', value:'Recommendation: property declaration as MLP is required by its semantic definition. As the property value is language independent, users are recommended to provide maximal 1 string in any language of the user’s choice.'})

CREATE (qualifiera9c21c:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (langstring7ba61e:LangString {lcode:'en', value:'12345'})

CREATE (multilanguageproperty022bc9:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'ZipCodeOfPOBox'})
CREATE (multilanguageproperty022bc9)-[:description]->(langstring5213d1)
CREATE (multilanguageproperty022bc9)-[:qualifier]->(qualifiera9c21c)
CREATE (multilanguageproperty022bc9)-[:value]->(langstring7ba61e)

CREATE (submodelelementcollection1d7c20:SubmodelElementCollection:SubmodelElement:Referable:Qualifiable {id_short:'ContactInformation'})
CREATE (submodelelementcollection1d7c20)-[:description]->(langstringd45bca)
CREATE (submodelelementcollection1d7c20)-[:qualifier]->(qualifier9f878d)
CREATE (submodelelementcollection1d7c20)-[:value]->(property6c4a75)
CREATE (submodelelementcollection1d7c20)-[:child]->(property6c4a75)
CREATE (submodelelementcollection1d7c20)-[:ids_RoleOfContactPerson]->(property6c4a75)
CREATE (submodelelementcollection1d7c20)-[:value]->(multilanguageproperty64c788)
CREATE (submodelelementcollection1d7c20)-[:child]->(multilanguageproperty64c788)
CREATE (submodelelementcollection1d7c20)-[:ids_NationalCode]->(multilanguageproperty64c788)
CREATE (submodelelementcollection1d7c20)-[:value]->(property65b3b1)
CREATE (submodelelementcollection1d7c20)-[:child]->(property65b3b1)
CREATE (submodelelementcollection1d7c20)-[:ids_Language]->(property65b3b1)
CREATE (submodelelementcollection1d7c20)-[:value]->(propertye676d2)
CREATE (submodelelementcollection1d7c20)-[:child]->(propertye676d2)
CREATE (submodelelementcollection1d7c20)-[:ids_TimeZone]->(propertye676d2)
CREATE (submodelelementcollection1d7c20)-[:value]->(multilanguageproperty4fe176)
CREATE (submodelelementcollection1d7c20)-[:child]->(multilanguageproperty4fe176)
CREATE (submodelelementcollection1d7c20)-[:ids_CityTown]->(multilanguageproperty4fe176)
CREATE (submodelelementcollection1d7c20)-[:value]->(multilanguagepropertyc52734)
CREATE (submodelelementcollection1d7c20)-[:child]->(multilanguagepropertyc52734)
CREATE (submodelelementcollection1d7c20)-[:ids_Company]->(multilanguagepropertyc52734)
CREATE (submodelelementcollection1d7c20)-[:value]->(multilanguageproperty9095b4)
CREATE (submodelelementcollection1d7c20)-[:child]->(multilanguageproperty9095b4)
CREATE (submodelelementcollection1d7c20)-[:ids_Department]->(multilanguageproperty9095b4)
CREATE (submodelelementcollection1d7c20)-[:value]->(submodelelementcollectione44334)
CREATE (submodelelementcollection1d7c20)-[:child]->(submodelelementcollectione44334)
CREATE (submodelelementcollection1d7c20)-[:ids_Phone]->(submodelelementcollectione44334)
CREATE (submodelelementcollection1d7c20)-[:value]->(submodelelementcollectionacc736)
CREATE (submodelelementcollection1d7c20)-[:child]->(submodelelementcollectionacc736)
CREATE (submodelelementcollection1d7c20)-[:ids_Email]->(submodelelementcollectionacc736)
CREATE (submodelelementcollection1d7c20)-[:value]->(multilanguageproperty0b836c)
CREATE (submodelelementcollection1d7c20)-[:child]->(multilanguageproperty0b836c)
CREATE (submodelelementcollection1d7c20)-[:ids_Street]->(multilanguageproperty0b836c)
CREATE (submodelelementcollection1d7c20)-[:value]->(multilanguageproperty3e36a1)
CREATE (submodelelementcollection1d7c20)-[:child]->(multilanguageproperty3e36a1)
CREATE (submodelelementcollection1d7c20)-[:ids_Zipcode]->(multilanguageproperty3e36a1)
CREATE (submodelelementcollection1d7c20)-[:value]->(multilanguagepropertyb61a88)
CREATE (submodelelementcollection1d7c20)-[:child]->(multilanguagepropertyb61a88)
CREATE (submodelelementcollection1d7c20)-[:ids_POBox]->(multilanguagepropertyb61a88)
CREATE (submodelelementcollection1d7c20)-[:value]->(multilanguageproperty022bc9)
CREATE (submodelelementcollection1d7c20)-[:child]->(multilanguageproperty022bc9)
CREATE (submodelelementcollection1d7c20)-[:ids_ZipCodeOfPOBox]->(multilanguageproperty022bc9)

CREATE (qualifiera42586:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (langstring3659b7:LangString {lcode:'en', value:'flow meter'})

CREATE (multilanguageproperty65ccf6:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'ManufacturerProductRoot'})
CREATE (multilanguageproperty65ccf6)-[:qualifier]->(qualifiera42586)
CREATE (multilanguageproperty65ccf6)-[:value]->(langstring3659b7)

CREATE (langstringbff2b8:LangString {lcode:'en', value:'Note: conditionally mandatory property according to EU Machine Directive 2006/42/EC. One of the two properties must be provided: ManufacturerProductFamily (0173-1#02-AAU731#001) or ManufacturerProductType (0173-1#02-AAO057#002). '})

CREATE (qualifier9cd010:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (langstringaf129c:LangString {lcode:'en', value:'Type ABC'})

CREATE (multilanguagepropertyaa0581:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'ManufacturerProductFamily'})
CREATE (multilanguagepropertyaa0581)-[:description]->(langstringbff2b8)
CREATE (multilanguagepropertyaa0581)-[:qualifier]->(qualifier9cd010)
CREATE (multilanguagepropertyaa0581)-[:value]->(langstringaf129c)

CREATE (langstring5ab9b2:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61987#ABA300#006 code of product Note: conditionally mandatory property according to EU Machine Directive 2006/42/EC. One of the two properties must be provided: ManufacturerProductFamily (0173-1#02-AAU731#001) or ManufacturerProductType (0173-1#02-AAO057#002). '})

CREATE (qualifierc8900d:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (langstringf403c8:LangString {lcode:'en', value:'FM-ABC-1234'})

CREATE (multilanguagepropertybb6859:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'ManufacturerProductType'})
CREATE (multilanguagepropertybb6859)-[:description]->(langstring5ab9b2)
CREATE (multilanguagepropertybb6859)-[:qualifier]->(qualifierc8900d)
CREATE (multilanguagepropertybb6859)-[:value]->(langstringf403c8)

CREATE (langstringae77ea:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61987#ABA951#007 serial number '})

CREATE (qualifierd4f014:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (property5e233b:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'SerialNumber', value_type:'str', value:'12345678'})
CREATE (property5e233b)-[:description]->(langstringae77ea)
CREATE (property5e233b)-[:qualifier]->(qualifierd4f014)

CREATE (langstring566dfd:LangString {lcode:'en', value:'Note: mandatory property according to EU Machine Directive 2006/42/EC. '})

CREATE (qualifier8b7fe1:Qualifier {type:'Multiplicity', value_type:'str', value:'One', kind:'CONCEPT_QUALIFIER'})

CREATE (property04000f:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'YearOfConstruction', value_type:'str', value:'2022'})
CREATE (property04000f)-[:description]->(langstring566dfd)
CREATE (property04000f)-[:qualifier]->(qualifier8b7fe1)

CREATE (langstringd83557:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61987#ABB757#007 date of manufacture Note: format by lexical representation: CCYY-MM-DD '})

CREATE (qualifierdac338:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (property3b97a9:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'DateOfManufacture', value_type:'Date', value:date('2022-01-01')})
CREATE (property3b97a9)-[:description]->(langstringd83557)
CREATE (property3b97a9)-[:qualifier]->(qualifierdac338)

CREATE (langstringf3f00c:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61987#ABA601#006 software version Note: Recommendation: property declaration as MLP is required by its semantic definition. As the property value is language independent, users are recommended to provide maximal 1 string in any language of the user’s choice.'})

CREATE (qualifier94110e:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (langstring64620f:LangString {lcode:'en', value:'1.0.0'})

CREATE (multilanguageproperty627ec8:MultiLanguageProperty:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'SoftwareVersion'})
CREATE (multilanguageproperty627ec8)-[:description]->(langstringf3f00c)
CREATE (multilanguageproperty627ec8)-[:qualifier]->(qualifier94110e)
CREATE (multilanguageproperty627ec8)-[:value]->(langstring64620f)

CREATE (langstringbbdc84:LangString {lcode:'en', value:'Note: see also [IRDI] 0112/2///61360_4#ADA034#001 country of origin Note: Country codes defined accord. to DIN EN ISO 3166-1 alpha-2 codes '})

CREATE (qualifier5be328:Qualifier {type:'Multiplicity', value_type:'str', value:'ZeroToOne', kind:'CONCEPT_QUALIFIER'})

CREATE (propertydad7d7:Property:DataElement:SubmodelElement:Referable:Qualifiable {id_short:'CountryOfOrigin', value_type:'str', value:'DE'})
CREATE (propertydad7d7)-[:description]->(langstringbbdc84)
CREATE (propertydad7d7)-[:qualifier]->(qualifier5be328)

CREATE (submodel1f33f6:Submodel:Identifiable:Referable:Qualifiable {kind:'TEMPLATE', id_short:'DigitalNameplate', id_:'https://admin-shell.io/idta/SubmodelTemplate/DigitalNameplate/2/0'})
CREATE (submodel1f33f6)-[:description]->(langstring99df2a)
CREATE (submodel1f33f6)-[:submodel_element]->(propertye7d1d7)
CREATE (submodel1f33f6)-[:child]->(propertye7d1d7)
CREATE (submodel1f33f6)-[:ids_URIOfTheProduct]->(propertye7d1d7)
CREATE (submodel1f33f6)-[:submodel_element]->(multilanguageproperty83daf9)
CREATE (submodel1f33f6)-[:child]->(multilanguageproperty83daf9)
CREATE (submodel1f33f6)-[:ids_ManufacturerName]->(multilanguageproperty83daf9)
CREATE (submodel1f33f6)-[:submodel_element]->(multilanguageproperty56e0db)
CREATE (submodel1f33f6)-[:child]->(multilanguageproperty56e0db)
CREATE (submodel1f33f6)-[:ids_ManufacturerProductDesignation]->(multilanguageproperty56e0db)
CREATE (submodel1f33f6)-[:submodel_element]->(submodelelementcollection1d7c20)
CREATE (submodel1f33f6)-[:child]->(submodelelementcollection1d7c20)
CREATE (submodel1f33f6)-[:ids_ContactInformation]->(submodelelementcollection1d7c20)
CREATE (submodel1f33f6)-[:submodel_element]->(multilanguageproperty65ccf6)
CREATE (submodel1f33f6)-[:child]->(multilanguageproperty65ccf6)
CREATE (submodel1f33f6)-[:ids_ManufacturerProductRoot]->(multilanguageproperty65ccf6)
CREATE (submodel1f33f6)-[:submodel_element]->(multilanguagepropertyaa0581)
CREATE (submodel1f33f6)-[:child]->(multilanguagepropertyaa0581)
CREATE (submodel1f33f6)-[:ids_ManufacturerProductFamily]->(multilanguagepropertyaa0581)
CREATE (submodel1f33f6)-[:submodel_element]->(multilanguagepropertybb6859)
CREATE (submodel1f33f6)-[:child]->(multilanguagepropertybb6859)
CREATE (submodel1f33f6)-[:ids_ManufacturerProductType]->(multilanguagepropertybb6859)
CREATE (submodel1f33f6)-[:submodel_element]->(property5e233b)
CREATE (submodel1f33f6)-[:child]->(property5e233b)
CREATE (submodel1f33f6)-[:ids_SerialNumber]->(property5e233b)
CREATE (submodel1f33f6)-[:submodel_element]->(property04000f)
CREATE (submodel1f33f6)-[:child]->(property04000f)
CREATE (submodel1f33f6)-[:ids_YearOfConstruction]->(property04000f)
CREATE (submodel1f33f6)-[:submodel_element]->(property3b97a9)
CREATE (submodel1f33f6)-[:child]->(property3b97a9)
CREATE (submodel1f33f6)-[:ids_DateOfManufacture]->(property3b97a9)
CREATE (submodel1f33f6)-[:submodel_element]->(multilanguageproperty627ec8)
CREATE (submodel1f33f6)-[:child]->(multilanguageproperty627ec8)
CREATE (submodel1f33f6)-[:ids_SoftwareVersion]->(multilanguageproperty627ec8)
CREATE (submodel1f33f6)-[:submodel_element]->(propertydad7d7)
CREATE (submodel1f33f6)-[:child]->(propertydad7d7)
CREATE (submodel1f33f6)-[:ids_CountryOfOrigin]->(propertydad7d7)

CREATE (assetadministrationshella73cea)-[:submodel]->(submodel1f33f6)
CREATE (UnresolvedRelationship208ea3:ModelReference:Reference:Generic:UnresolvedRelationship {type:'SUBMODEL', value:'https://admin-shell.io/zvei/nameplate/2/0/Nameplate'})
CREATE (submodel1f33f6)-[:semantic_id]->(UnresolvedRelationship208ea3)
CREATE (UnresolvedRelationship6eb1ae:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAY811#001'})
CREATE (propertye7d1d7)-[:semantic_id]->(UnresolvedRelationship6eb1ae)
CREATE (UnresolvedRelationship3cd686:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO677#002'})
CREATE (multilanguageproperty83daf9)-[:semantic_id]->(UnresolvedRelationship3cd686)
CREATE (UnresolvedRelationship849616:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAW338#001'})
CREATE (multilanguageproperty56e0db)-[:semantic_id]->(UnresolvedRelationship849616)
CREATE (UnresolvedRelationship6c9ab5:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation'})
CREATE (submodelelementcollection1d7c20)-[:semantic_id]->(UnresolvedRelationship6c9ab5)
CREATE (UnresolvedRelationship92adca:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO204#003'})
CREATE (property6c4a75)-[:semantic_id]->(UnresolvedRelationship92adca)
CREATE (UnresolvedRelationship6ca9c9:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO134#002'})
CREATE (multilanguageproperty64c788)-[:semantic_id]->(UnresolvedRelationship6ca9c9)
CREATE (UnresolvedRelationship1cd3b5:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/Language'})
CREATE (property65b3b1)-[:semantic_id]->(UnresolvedRelationship1cd3b5)
CREATE (UnresolvedRelationshipb9bf7a:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/TimeZone'})
CREATE (propertye676d2)-[:semantic_id]->(UnresolvedRelationshipb9bf7a)
CREATE (UnresolvedRelationship6a6451:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO132#002'})
CREATE (multilanguageproperty4fe176)-[:semantic_id]->(UnresolvedRelationship6a6451)
CREATE (UnresolvedRelationship211810:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAW001#001'})
CREATE (multilanguagepropertyc52734)-[:semantic_id]->(UnresolvedRelationship211810)
CREATE (UnresolvedRelationship669f86:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO127#003'})
CREATE (multilanguageproperty9095b4)-[:semantic_id]->(UnresolvedRelationship669f86)
CREATE (UnresolvedRelationshipe9b9db:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/Phone'})
CREATE (submodelelementcollectione44334)-[:semantic_id]->(UnresolvedRelationshipe9b9db)
CREATE (UnresolvedRelationship701a14:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO136#002'})
CREATE (multilanguageproperty7b5420)-[:semantic_id]->(UnresolvedRelationship701a14)
CREATE (UnresolvedRelationship9df906:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO137#003'})
CREATE (property14e9df)-[:semantic_id]->(UnresolvedRelationship9df906)
CREATE (UnresolvedRelationship935d4d:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'https://admin-shell.io/zvei/nameplate/1/0/ContactInformations/ContactInformation/AvailableTime/'})
CREATE (multilanguagepropertyeb59ba)-[:semantic_id]->(UnresolvedRelationship935d4d)
CREATE (UnresolvedRelationship2c0025:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAQ836#005'})
CREATE (submodelelementcollectionacc736)-[:semantic_id]->(UnresolvedRelationship2c0025)
CREATE (UnresolvedRelationship83194d:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO198#002'})
CREATE (property9fb0f0)-[:semantic_id]->(UnresolvedRelationship83194d)
CREATE (UnresolvedRelationshipe12498:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO200#002'})
CREATE (multilanguageproperty2ccb7e)-[:semantic_id]->(UnresolvedRelationshipe12498)
CREATE (UnresolvedRelationship43242d:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO199#003'})
CREATE (property787b63)-[:semantic_id]->(UnresolvedRelationship43242d)
CREATE (UnresolvedRelationshipe8f6dc:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO201#002'})
CREATE (multilanguageproperty9caa30)-[:semantic_id]->(UnresolvedRelationshipe8f6dc)
CREATE (UnresolvedRelationship63127f:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO128#002'})
CREATE (multilanguageproperty0b836c)-[:semantic_id]->(UnresolvedRelationship63127f)
CREATE (UnresolvedRelationship80e7b7:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO129#002'})
CREATE (multilanguageproperty3e36a1)-[:semantic_id]->(UnresolvedRelationship80e7b7)
CREATE (UnresolvedRelationship92f93b:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO130#002'})
CREATE (multilanguagepropertyb61a88)-[:semantic_id]->(UnresolvedRelationship92f93b)
CREATE (UnresolvedRelationshipc6d41e:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO131#002'})
CREATE (multilanguageproperty022bc9)-[:semantic_id]->(UnresolvedRelationshipc6d41e)
CREATE (UnresolvedRelationship2890fb:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAU732#001'})
CREATE (multilanguageproperty65ccf6)-[:semantic_id]->(UnresolvedRelationship2890fb)
CREATE (UnresolvedRelationship5a1050:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAU731#001'})
CREATE (multilanguagepropertyaa0581)-[:semantic_id]->(UnresolvedRelationship5a1050)
CREATE (UnresolvedRelationshipb80ad8:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO057#002'})
CREATE (multilanguagepropertybb6859)-[:semantic_id]->(UnresolvedRelationshipb80ad8)
CREATE (UnresolvedRelationship75b33c:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAM556#002'})
CREATE (property5e233b)-[:semantic_id]->(UnresolvedRelationship75b33c)
CREATE (UnresolvedRelationship32ef88:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAP906#001'})
CREATE (property04000f)-[:semantic_id]->(UnresolvedRelationship32ef88)
CREATE (UnresolvedRelationship04d8c5:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAR972#002'})
CREATE (property3b97a9)-[:semantic_id]->(UnresolvedRelationship04d8c5)
CREATE (UnresolvedRelationship7eb565:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAM737#002'})
CREATE (multilanguageproperty627ec8)-[:semantic_id]->(UnresolvedRelationship7eb565)
CREATE (UnresolvedRelationshipb9c61c:ExternalReference:Reference:UnresolvedRelationship {type:'GLOBAL_REFERENCE', value:'0173-1#02-AAO259#004'})
CREATE (propertydad7d7)-[:semantic_id]->(UnresolvedRelationshipb9c61c)
